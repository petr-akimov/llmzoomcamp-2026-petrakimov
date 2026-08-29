# get IP-address from the LoadBalancer of Ingress-controller
data "kubernetes_service_v1" "ingress_nginx" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = "zoomcamp"
  }
  depends_on = [
    helm_release.ingress_nginx
  ]
}

resource "yandex_dns_zone" "main_zone" {
  name   = "akimovp-ru"
  zone   = "akimovp.ru."
  public = true
}

resource "yandex_dns_recordset" "a_root" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_www" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "www.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_apps" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "apps.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_rag" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "rag.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_grafana" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "grafana.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_airflow" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "airflow.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

resource "yandex_dns_recordset" "a_ui" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "ui.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service_v1.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}
