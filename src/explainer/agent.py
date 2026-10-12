import os
import time
import json
import logging
from typing import Dict, Any, Optional
import httpx
from src.explainer.fallback import RuleBasedExplainerFallback

logger = logging.getLogger("forecast_explainer")

class GeminiIncidentExplainer:
    """
    GenAI Incident Explainer powered by Gemini / Vertex AI.
    Synthesizes drift alerts and forecast errors into structured root-cause analyses citing exact metrics.
    Automatically degrades to deterministic RuleBasedExplainerFallback on API timeout or failure.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        use_vertex: Optional[bool] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"
        self.use_vertex = use_vertex if use_vertex is not None else (
            os.getenv("USE_VERTEX_AI", "false").lower() in ("true", "1") or bool(self.project)
        )
        self.fallback = RuleBasedExplainerFallback()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai
            if self.use_vertex:
                self._client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=self.location
                )
            elif self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            return self._client
        except Exception:
            return None

    def explain(self, incident_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates incident explanation.
        Tries Gemini/Vertex AI via google-genai SDK first; falls back to rule-based engine if unavailable.
        """
        start_time = time.perf_counter()
        prompt = self._build_prompt(incident_context)

        # 1. Try google-genai SDK with Vertex AI or API key
        try:
            client = self._get_client()
            if client is not None:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                text = response.text
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                cited_metrics = self._extract_cited_metrics(text, incident_context)
                return {
                    "source": "VERTEX_AI" if self.use_vertex else "GEMINI_API",
                    "incident_type": incident_context.get("incident_type", "DRIFT_ALERT"),
                    "explanation": text,
                    "cited_metrics": cited_metrics,
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": 350
                }
        except Exception as e:
            logger.warning(f"google-genai call failed in explainer: {e}")

        # 2. Try HTTP API if API key exists
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 800
                    }
                }
                with httpx.Client(timeout=5.0) as http_client:
                    response = http_client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        latency_ms = (time.perf_counter() - start_time) * 1000.0
                        cited_metrics = self._extract_cited_metrics(text, incident_context)
                        return {
                            "source": "GEMINI_API",
                            "incident_type": incident_context.get("incident_type", "DRIFT_ALERT"),
                            "explanation": text,
                            "cited_metrics": cited_metrics,
                            "latency_ms": round(latency_ms, 2),
                            "tokens_used": 350
                        }
            except Exception:
                pass

        logger.info("Using rule-based fallback explainer.")
        res = self.fallback.explain(incident_context)
        res["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
        res["tokens_used"] = 0
        return res

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are an expert Principal MLOps & Demand Forecasting System Incident Engineer.\n"
            "An automated monitoring alert fired for an active retail demand forecast model.\n\n"
            "Here is the quantitative telemetry:\n"
            f"{json.dumps(context, indent=2)}\n\n"
            "Provide a concise, executive-ready Incident & Root Cause Explanation.\n"
            "MANDATORY REQUIREMENTS:\n"
            "1. You MUST explicitly cite the quantitative numbers from the telemetry (e.g. PSI, WAPE, Bias, percentage shifts).\n"
            "2. Identify the root cause (e.g. price elasticity shift, promotional surge, covariate drift, concept drift).\n"
            "3. State the operational impact on supply chain (stockouts vs excess inventory holding cost).\n"
            "4. Prescribe specific remediation actions (retrain on shifted slice, adjust safety stock, rollback model)."
        )

    def _extract_cited_metrics(self, text: str, context: Dict[str, Any]) -> list:
        cited = []
        metrics = context.get("metrics", {})
        drift = context.get("drift_report", {})
        if str(drift.get("max_psi", "")) in text:
            cited.append(f"Max PSI: {drift.get('max_psi')}")
        if f"{metrics.get('wape', 0):.2f}" in text or f"{metrics.get('wape', 0)*100:.1f}" in text:
            cited.append(f"WAPE: {metrics.get('wape')}")
        if f"{metrics.get('bias', 0):.2f}" in text or f"{metrics.get('bias', 0)*100:.1f}" in text:
            cited.append(f"Bias: {metrics.get('bias')}")
        return cited
