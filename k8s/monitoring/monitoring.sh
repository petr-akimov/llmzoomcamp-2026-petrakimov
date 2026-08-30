#!/usr/bin/env bash
set -euo pipefail

# Гарантируем, что скрипт выполняется относительно корня репозитория
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== 1. Добавление и обновление Helm-репозитория ==="
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

echo "=== 2. Создание Namespace ==="
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "=== 3. Развертывание kube-prometheus-stack ==="
helm upgrade --install kp prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring/01-kube-prom-values.yaml

echo "=== 4. Ожидание готовности пода Grafana ==="
kubectl -n monitoring wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=180s

echo "=== 5. Применение ресурсов мониторинга ==="
kubectl apply -f k8s/monitoring/04-grafana-dashboards.yaml
kubectl apply -f k8s/monitoring/08-servicemonitor.yaml
kubectl apply -f k8s/monitoring/05-grafana-ingress.yaml

echo "=== 6. Проверка статуса компонентов ==="
echo "--- Grafana Pods ---"
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

echo "--- Prometheus Pods ---"
kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus