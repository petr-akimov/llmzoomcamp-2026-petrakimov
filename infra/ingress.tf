# ingress-nginx – динамический LoadBalancer
resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "zoomcamp"
  create_namespace = true

  values = [<<EOF
controller:
  replicaCount: 1
  service:
    type: LoadBalancer
    externalTrafficPolicy: Local
  admissionWebhooks:
    enabled: false
EOF
  ]

  depends_on = [
    yandex_kubernetes_node_group.akimovp_nodes
  ]
}

