resource "yandex_iam_service_account" "sa" {
  name        = var.name
  description = "Service account for Airflow management"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_roles" {
  for_each = toset([
    "storage.editor"
  ])

  folder_id = var.provider_config.folder_id
  role      = each.key
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = yandex_iam_service_account.sa.id
  description        = "Static access key for service account"
}

resource "yandex_iam_service_account_key" "sa_auth_key" {
  service_account_id = yandex_iam_service_account.sa.id
}

