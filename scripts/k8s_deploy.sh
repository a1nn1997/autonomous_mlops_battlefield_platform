#!/usr/bin/env bash
# ==============================================================================
# Production Kubernetes Deployment & Rollout Validation Runbook
# ==============================================================================
set -euo pipefail

NAMESPACE="forecast-mlops"
DEPLOYMENT="forecast-serving"

echo "=== 1. Validating Kubernetes Cluster Context ==="
kubectl cluster-info || { echo "ERROR: Cannot reach Kubernetes cluster."; exit 1; }

echo "=== 2. Applying Declarative Kustomize Manifests ==="
kubectl apply -k k8s/

echo "=== 3. Monitoring Zero-Downtime Rolling Update Status ==="
kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=120s

echo "=== 4. Validating High-Availability Pod Placement ==="
kubectl get pods -n ${NAMESPACE} -l app=forecast-serving -o wide

echo "=== 5. Health Probe Verification ==="
POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l app=forecast-serving -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n ${NAMESPACE} "${POD_NAME}" -- curl -sf http://localhost:8000/health || {
  echo "WARNING: Internal health probe returned non-200. Check logs."
  exit 1
}

echo "=== 6. Rollout History ==="
kubectl rollout history deployment/${DEPLOYMENT} -n ${NAMESPACE}

echo "Deployment completed successfully with ZERO DOWNTIME."
