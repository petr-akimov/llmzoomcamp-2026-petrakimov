# Получаем IP адрес LoadBalancer'а Ingress-контроллера
data "kubernetes_service" "ingress_nginx" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = "zoomcamp"
  }
  depends_on = [
    helm_release.ingress_nginx
  ]
}

# Создаём публичную DNS-зону
resource "yandex_dns_zone" "main_zone" {
  name   = "akimovp-ru"
  zone   = "akimovp.ru."
  public = true
}

# A-запись для корневого домена
resource "yandex_dns_recordset" "a_root" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

# A-запись для www
resource "yandex_dns_recordset" "a_www" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "www.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

# A-запись для apps
resource "yandex_dns_recordset" "a_apps" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "apps.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

# A-запись для www
resource "yandex_dns_recordset" "a_rag" {
  zone_id = yandex_dns_zone.main_zone.id
  name    = "rag.akimovp.ru."
  type    = "A"
  ttl     = 300
  data    = [data.kubernetes_service.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}
