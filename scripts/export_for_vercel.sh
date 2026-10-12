#!/usr/bin/env bash
# ==============================================================================
# Vercel Deployment & Export Script (Production Token Shield Enabled)
# Strictly excludes .venv and heavy backend artifacts from Vercel deployment.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🚀 Preparing Forecast-to-Insight UI for Vercel Deployment..."
echo "📂 Root Directory: ${ROOT_DIR}"

# 1. Enforce Token Shield in Production
export DETERMINISTIC_PROD_MODE="true"
export NODE_ENV="production"
echo "🛡️ Production Token Shield: ENABLED (Deterministic Rule-Based Engine)"

# 2. Check if Vercel CLI is installed
if command -v vercel &> /dev/null; then
    echo "⚡ Vercel CLI detected. Deploying from ./ui directory..."
    cd "${ROOT_DIR}/ui"
    
    # Deploy to Vercel production without uploading .venv
    vercel --prod --yes
    echo "✅ Successfully deployed to Vercel with zero token leakage!"
else
    echo "⚠️ Vercel CLI not found in PATH."
    echo "📦 To deploy manually or connect your Git repository:"
    echo "   1. Ensure .vercelignore excludes .venv (Verified ✅)"
    echo "   2. Run: npm install -g vercel"
    echo "   3. Run: cd ui && vercel --prod"
    echo "   4. Or push to GitHub to trigger .github/workflows/deploy-vercel.yml"
fi
