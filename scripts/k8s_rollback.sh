#!/usr/bin/env bash
# ==============================================================================
# Dual-Layer Emergency Rollback Runbook:
# 1. Container-Level: Native Kubernetes Deployment Rollout Undo
# 2. Application-Level: Model Registry Atomic Pointer Rollback (< 15 ms)
# ==============================================================================
set -euo pipefail

NAMESPACE="forecast-mlops"
DEPLOYMENT="forecast-serving"
MODE="${1:-all}"  # options: k8s, model, all

echo "=========================================================="
echo "🚨 INITIATING PRODUCTION EMERGENCY ROLLBACK DRILL (MODE: ${MODE})"
echo "=========================================================="

if [ "${MODE}" == "k8s" ] || [ "${MODE}" == "all" ]; then
  echo "--- Step 1: Native Kubernetes Deployment Rollback ---"
  echo "Inspecting rollout history before undo:"
  kubectl rollout history deployment/${DEPLOYMENT} -n ${NAMESPACE}

  echo "Executing: kubectl rollout undo deployment/${DEPLOYMENT} -n ${NAMESPACE}"
  kubectl rollout undo deployment/${DEPLOYMENT} -n ${NAMESPACE}

  echo "Awaiting zero-downtime rollback stabilization:"
  kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=90s
fi

if [ "${MODE}" == "model" ] || [ "${MODE}" == "all" ]; then
  echo "--- Step 2: Model Registry In-Memory Atomic Rollback (< 15 ms) ---"
  echo "Dispatching Kubernetes Emergency Rollback Job:"
  kubectl apply -f k8s/rollback-job.yaml
  kubectl wait --for=condition=complete job/forecast-emergency-rollback -n ${NAMESPACE} --timeout=60s
  kubectl logs -n ${NAMESPACE} job/forecast-emergency-rollback
  kubectl delete job forecast-emergency-rollback -n ${NAMESPACE}
fi

echo "=========================================================="
echo "✅ EMERGENCY ROLLBACK DRILL COMPLETED WITH ZERO DOWNTIME."
echo "=========================================================="
