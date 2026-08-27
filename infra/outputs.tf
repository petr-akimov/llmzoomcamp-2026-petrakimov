output "ingress_ip" {
  value = data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip
  description = "Dynamic public IP of the Ingress LoadBalancer"
}

output "cluster_name" {
  value = yandex_kubernetes_cluster.akimovp_cluster.name
}

output "s3_bucket_name" {
  value       = yandex_storage_bucket.bucket.bucket
  description = "Created S3 Bucket Name"
}
