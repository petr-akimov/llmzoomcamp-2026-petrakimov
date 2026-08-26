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
