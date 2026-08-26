import glob
import os
import re
import sys

from dotenv import load_dotenv
from fastembed import TextEmbedding
import lancedb
from lancedb.index import FTS
from pypdf import PdfReader

load_dotenv()

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
TABLE_NAME: str = os.getenv("TABLE_NAME", "pdf_vectors")

S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "https://storage.yandexcloud.net")
AWS_REGION: str = os.getenv("AWS_REGION", "ru-central1")


def normalize_text(text: str) -> str:
    """Убирает разрывы слов на стыке строк и лишние переносы."""
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_text_from_pdfs(data_dir: str = "./data") -> list[dict]:
    """Парсит PDF-файлы, объединяет страницы и нарезает оптимальные чанки (~700 символов) для ускорения инференса."""
    documents = []
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))

    if not pdf_files:
        print(f"[!] Файлы .pdf в директории '{data_dir}' не найдены.")
        return documents

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Обработка файла: {filename}...")
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            page_map = []  # Хранит номер страницы для каждого символа в full_text

            # 1. Склеиваем весь документ в один поток
            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text()
                if raw_text and raw_text.strip():
                    cleaned = normalize_text(raw_text) + " "
                    full_text += cleaned
                    page_map.extend([idx + 1] * len(cleaned))

            if not full_text:
                continue

            # 2. Оптимизированное чанкование (700 символов ≈ 110-130 слов)
            # Короткие чанки существенно ускоряют Prompt Processing Time на CPU
            chunk_size = 700
            chunk_overlap = 120
            start = 0

            while start < len(full_text):
                end = start + chunk_size

                if end < len(full_text):
                    # Ищем ближайшую точку, чтобы не разрывать предложения
                    last_dot = full_text.rfind('. ', start, end)
                    if last_dot > start + (chunk_size // 2):
                        end = last_dot + 1
                    else:
                        # Если точки нет, ищем пробел
                        last_space = full_text.rfind(' ', start, end)
                        if last_space > start + (chunk_size // 2):
                            end = last_space

                chunk = full_text[start:end].strip()
                if len(chunk) > 40:
                    page_num = page_map[start]
                    documents.append({
                        "text": chunk,
                        "metadata": f"{filename}#page={page_num}",
                    })

                start += chunk_size - chunk_overlap

        except Exception as e:
            print(f"[!] Ошибка при чтении {filename}: {e}")

    return documents


def run_ingestion() -> None:
    docs = extract_text_from_pdfs()
    if not docs:
        print("[!] Процесс остановлен: нет данных для векторизации.")
        sys.exit(1)

    print(f"Извлечено {len(docs)} текстовых чанков.")

    print(f"Загрузка модели эмбеддингов: {EMBEDDING_MODEL}...")
    embedder = TextEmbedding(model_name=EMBEDDING_MODEL)

    print("Векторизация текстов...")
    texts = [doc["text"] for doc in docs]
    vectors = list(embedder.embed(texts))

    data = []
    for doc, vector in zip(docs, vectors):
        data.append({
            "vector": vector.tolist(),
            "text": doc["text"],
            "metadata": doc["metadata"],
        })

    s3_uri = f"s3://{S3_BUCKET_NAME}/lancedb"
    print(f"Подключение к LanceDB S3 по адресу: {s3_uri}")

    storage_options = {
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_KEY,
        "aws_region": AWS_REGION,
        "aws_endpoint": S3_ENDPOINT_URL,
        "allow_http": "true" if S3_ENDPOINT_URL.startswith("http://") else "false",
    }

    try:
        db = lancedb.connect(s3_uri, storage_options=storage_options)
        print(f"Запись таблицы '{TABLE_NAME}' в Yandex Object Storage...")
        tbl = db.create_table(TABLE_NAME, data=data, mode="overwrite")
        tbl.create_index("text", config=FTS(), replace=True)
        print("Успешно! Индексация завершена.")
    except Exception as e:
        print(f"[!] Ошибка записи в LanceDB/S3: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_ingestion()