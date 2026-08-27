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
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_text_from_pdfs(data_dir: str = "./data") -> list[dict]:
    documents = []
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))

    if not pdf_files:
        print(f"[!] Files .pdf not found in the directory '{data_dir}'.")
        return documents

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Parsing file: {filename}...")
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            page_map = []  

            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text()
                if raw_text and raw_text.strip():
                    cleaned = normalize_text(raw_text) + " "
                    full_text += cleaned
                    page_map.extend([idx + 1] * len(cleaned))

            if not full_text:
                continue

            chunk_size = 700
            chunk_overlap = 120
            start = 0

            while start < len(full_text):
                end = start + chunk_size

                if end < len(full_text):
                    last_dot = full_text.rfind('. ', start, end)
                    if last_dot > start + (chunk_size // 2):
                        end = last_dot + 1
                    else:
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
            print(f"[!] Error reasing file {filename}: {e}")

    return documents


def run_ingestion() -> None:
    docs = extract_text_from_pdfs()
    if not docs:
        print("[!] Parsing stopped - No data for vectorisation.")
        sys.exit(1)

    print(f"Extracted {len(docs)} text chunks.")

    print(f"Embedding model is been loading: {EMBEDDING_MODEL}...")
    embedder = TextEmbedding(model_name=EMBEDDING_MODEL)

    print("Text vectorization in progress...")
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
    print(f"Connected to LanceDB S3: {s3_uri}")

    storage_options = {
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_KEY,
        "aws_region": AWS_REGION,
        "aws_endpoint": S3_ENDPOINT_URL,
        "allow_http": "true" if S3_ENDPOINT_URL.startswith("http://") else "false",
    }

    try:
        db = lancedb.connect(s3_uri, storage_options=storage_options)
        print(f"Table '{TABLE_NAME}' written into S3")
        tbl = db.create_table(TABLE_NAME, data=data, mode="overwrite")
        tbl.create_index("text", config=FTS(), replace=True)
        print("Successful! Indexing completed.")
    except Exception as e:
        print(f"[!] Write error into LanceDB/S3: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_ingestion()