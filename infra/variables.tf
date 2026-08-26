variable "yc_token" {
  type        = string
  description = "Yandex Cloud OAuth token"
  sensitive   = true
}

variable "yc_cloud_id" {
  type        = string
  description = "Yandex Cloud ID"
  sensitive   = true
}

variable "yc_folder_id" {
  type        = string
  description = "Yandex Cloud Folder ID"
  sensitive   = true
}

variable "yc_zone" {
  type        = string
  description = "Yandex Cloud zone"
  default     = "ru-central1-a"
}

variable "yc_bucket_name" {
  type        = string
  description = "Base name for S3 bucket (will be suffixed)"
  default     = "akimovp-bucket"
}

# Service account for S3 bucket
variable "yc_service_account_name" {
  type        = string
  description = "Name of S3 bucket service account"
  default     = "s3-sa"
}

variable "kubeconfig_path" {
  description = "path to kubeconfig"
  type        = string
  default     = "../kubeconfig.yaml"
}

variable "yc_instance_name" {
  type        = string
  description = "Name of the virtual machine"
  default     = "akimovp-proxy-vm"
}

variable "yc_image_id" {
  type        = string
  description = "ID of the image for the virtual machine"
  default     = "fd808e721rc1vt7jkd0o"
}

variable "public_key_path" {
  type        = string
  description = "Path to the public key file"
  default     = "~/.ssh/id_rsa.pub"
}

variable "private_key_path" {
  type        = string
  description = "Path to the private key file"
  default     = "~/.ssh/id_rsa"
}

variable "yc_security_group_name" {
  type        = string
  description = "Name of the security group"
  default     = "akimovp-security-group"
}

variable "yc_storage_endpoint_url" {
  type        = string
  description = "Yandex Object Storage Endpoint URL"
  default     = "https://storage.yandexcloud.net"
}

# Объект конфигурации для передачи в модуль ./modules/iam-s3
locals {
  yc_config = {
    zone      = var.yc_zone
    folder_id = var.yc_folder_id
    token     = var.yc_token
    cloud_id  = var.yc_cloud_id
  }
}

