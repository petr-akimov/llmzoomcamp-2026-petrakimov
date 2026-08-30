module "iam-s3" {
  source = "./modules/iam-s3"
  name   = var.yc_service_account_name
  provider_config = {
    zone      = var.yc_zone
    folder_id = var.yc_folder_id
    token     = var.yc_token
    cloud_id  = var.yc_cloud_id
  }
}

resource "random_id" "bucket_id" {
  byte_length = 8
}

resource "yandex_storage_bucket" "bucket" {
  bucket        = "${var.yc_bucket_name}-${random_id.bucket_id.hex}"
  access_key    = module.iam-s3.access_key
  secret_key    = module.iam-s3.secret_key
  force_destroy = true
  depends_on    = [module.iam-s3]
}

resource "local_file" "variables_file" {
  content = jsonencode({
    # S3
    S3_ENDPOINT_URL = var.yc_storage_endpoint_url
    S3_ACCESS_KEY   = module.iam-s3.access_key
    S3_SECRET_KEY   = module.iam-s3.secret_key
    S3_BUCKET_NAME  = yandex_storage_bucket.bucket.bucket
  })
  filename        = "./variables.json"
  file_permission = "0600"
}


resource "local_file" "env_file" {
  content = <<-EOT
    EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
    TABLE_NAME=pdf_vectors
    S3_BUCKET_NAME=${yandex_storage_bucket.bucket.bucket}
    S3_ACCESS_KEY=${module.iam-s3.access_key}
    S3_SECRET_KEY=${module.iam-s3.secret_key}
    S3_ENDPOINT_URL=${var.yc_storage_endpoint_url}
    AWS_REGION=ru-central1
    LLM_MODEL_NAME=qwen2.5:1.5b
    OLLAMA_URL=http://apps.akimovp.ru/api/generate

  EOT
  filename        = "../.env"
  file_permission = "0644"
  depends_on      = [yandex_storage_bucket.bucket, module.iam-s3]
}

resource "local_file" "k8s_secret" {
  content = <<-EOT
---
apiVersion: v1
kind: Secret
metadata:
  name: rag-service-secrets
type: Opaque
stringData:
  S3_ACCESS_KEY: "${module.iam-s3.access_key}"
  S3_SECRET_KEY: "${module.iam-s3.secret_key}"
EOT
  filename        = "../k8s/rag_llm/secret-rag.yaml"
  file_permission = "0644"
  depends_on      = [module.iam-s3]
}

resource "local_file" "k8s_configmap" {
  content = <<-EOT
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-service-config
data:
  EMBEDDING_MODEL: "BAAI/bge-small-en-v1.5"
  TABLE_NAME: "pdf_vectors"
  S3_BUCKET_NAME: "${yandex_storage_bucket.bucket.bucket}"
  S3_ENDPOINT_URL: "${var.yc_storage_endpoint_url}"
  AWS_REGION: "ru-central1"
  LLM_MODEL_NAME: "qwen2.5:1.5b"
  OLLAMA_URL: "http://ollama-qwen-service.default.svc.cluster.local:11434/api/generate"
EOT
  filename        = "../k8s/rag_llm/configmap-rag.yaml"
  file_permission = "0644"
  depends_on      = [yandex_storage_bucket.bucket]
}