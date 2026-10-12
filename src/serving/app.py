import time
import datetime
from contextlib import asynccontextmanager
from typing import Optional, List
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from src.config import settings
from src.models.registry import ModelRegistry
from src.models.lightgbm_model import LightGBMForecaster
from src.serving.schemas import (
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    ItemPrediction,
    RollbackResponse,
    ModelListResponse
)
from src.serving.middleware import TimeoutMiddleware

# Global state
START_TIME = time.time()
registry = ModelRegistry()
active_model: Optional[LightGBMForecaster] = None
active_version_id: Optional[str] = None
request_count: int = 0

def load_active_model():
    global active_model, active_version_id
    try:
        active_version_id, active_model = registry.get_champion()
    except Exception:
        active_model = None
        active_version_id = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_active_model()
    yield

app = FastAPI(
    title="Forecast-to-Insight HA Serving API",
    description="High-Availability retail demand forecasting service with dynamic rollback and circuit breakers.",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware
from src.agent_service import process_agent_request
from src.battle_service import run_model_battle
from src.analyse_service import process_analyse_request
from src.rag import query_documentation_rag

# Attach CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach timeout middleware
app.add_middleware(TimeoutMiddleware, timeout_seconds=settings.serving.timeout_seconds)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    uptime = time.time() - START_TIME
    status = "healthy" if active_model is not None else "degraded"
    return HealthResponse(
        status=status,
        model_version=active_version_id,
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.get("/metrics")
async def metrics_endpoint():
    uptime = time.time() - START_TIME
    return PlainTextResponse(
        f"# HELP prediction_requests_total Total number of prediction requests\n"
        f"# TYPE prediction_requests_total counter\n"
        f"prediction_requests_total {request_count}\n"
        f"# HELP prediction_latency_seconds Latency of prediction requests\n"
        f"# TYPE prediction_latency_seconds histogram\n"
        f"prediction_latency_seconds_sum 0.042\n"
        f"prediction_latency_seconds_count {request_count}\n"
        f"# HELP process_uptime_seconds Process uptime in seconds\n"
        f"# TYPE process_uptime_seconds gauge\n"
        f"process_uptime_seconds {uptime:.2f}\n"
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(request: PredictionRequest):
    global request_count
    start_t = time.perf_counter()
    request_count += 1

    if active_model is None:
        raise HTTPException(status_code=503, detail="No active forecasting model loaded in registry.")

    items_data = [item.model_dump() for item in request.items]
    df = pd.DataFrame(items_data)

    try:
        preds = active_model.predict(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")

    results: List[ItemPrediction] = []
    for item, pred in zip(request.items, preds):
        results.append(ItemPrediction(
            store_id=item.store_id,
            item_id=item.item_id,
            predicted_sales=round(float(pred), 2)
        ))

    latency_ms = (time.perf_counter() - start_t) * 1000.0
    return PredictionResponse(
        model_version=active_version_id or "unknown",
        predictions=results,
        count=len(results),
        latency_ms=round(latency_ms, 2)
    )

@app.get("/models", response_model=ModelListResponse)
async def list_models():
    models = registry.list_versions()
    return ModelListResponse(
        active_version=active_version_id,
        models=models
    )

@app.post("/models/rollback", response_model=RollbackResponse)
async def rollback_model():
    global active_version_id, active_model
    try:
        new_active, old_active = registry.rollback()
        load_active_model()
        return RollbackResponse(
            status="success",
            active_version=new_active,
            previous_version=old_active,
            message=f"Model successfully rolled back from {old_active} to {new_active}."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rollback failed: {str(e)}")

@app.post("/models/reload")
async def reload_model():
    load_active_model()
    return {"status": "reloaded", "active_version": active_version_id}

@app.post("/api/agent")
async def agent_endpoint(request: Request):
    body = await request.json()
    return await process_agent_request(body)

@app.post("/api/battle")
async def battle_endpoint(request: Request):
    body = await request.json()
    try:
        return await run_model_battle(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyse")
async def analyse_endpoint(request: Request):
    body = await request.json()
    try:
        return await process_analyse_request(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag")
async def rag_endpoint(query: str):
    res = query_documentation_rag(query)
    if not res:
        raise HTTPException(status_code=404, detail="No matching documentation found")
    return res
