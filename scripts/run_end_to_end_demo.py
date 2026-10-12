#!/usr/bin/env python3
"""
Executable script for running the Forecast-to-Insight end-to-end demo.
Demonstrates:
  1. Data ingestion & feature pipeline
  2. Baseline evaluation (Naive & Seasonal Naive)
  3. LightGBM model training & WAPE validation
  4. Distribution drift injection & PSI detection
  5. GenAI incident explainer RCA
  6. Automated shadow retraining & promotion gate
  7. Emergency atomic rollback
  8. 32-case Golden Dataset benchmark (Gemini vs OpenAI)
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.demo import run_full_demo

if __name__ == "__main__":
    run_full_demo()
