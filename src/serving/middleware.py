import asyncio
import time
import logging
from typing import Callable, Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import httpx

logger = logging.getLogger("forecast_serving")

fallback_counter: int = 0

class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Terminates long-running inference requests exceeding timeout_seconds.
    For /predict, gracefully returns a Seasonal Naive (t-7) fallback with HTTP 200 and served_by: fallback.
    """
    def __init__(self, app, timeout_seconds: float = 2.0):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable):
        global fallback_counter
        timeout = self.timeout_seconds if request.url.path.startswith("/predict") else 30.0
        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Request {request.url.path} timed out after {timeout}s. Engaging seasonal-naive fallback.")
            if request.url.path.startswith("/predict"):
                fallback_counter += 1
                try:
                    body = await request.json()
                    items = body.get("items", [])
                    fallback_preds = []
                    for it in items:
                        val = it.get("lag_7")
                        if val is None:
                            val = it.get("lag_1", 25.0)
                        fallback_preds.append({
                            "store_id": it.get("store_id", "STORE_01"),
                            "item_id": it.get("item_id", "ITEM_001"),
                            "predicted_sales": round(float(val), 2)
                        })
                    return JSONResponse(
                        status_code=200,
                        content={
                            "model_version": "fallback_seasonal_naive",
                            "predictions": fallback_preds,
                            "count": len(fallback_preds),
                            "latency_ms": round(timeout * 1000.0, 2),
                            "served_by": "fallback"
                        }
                    )
                except Exception:
                    pass
            return JSONResponse(
                status_code=504,
                content={"detail": f"Request processing timed out after {timeout} seconds"}
            )

async def predict_with_retry(
    url: str,
    payload: Dict[str, Any],
    max_retries: int = 3,
    backoff_factor: float = 0.2,
    timeout: float = 2.0
) -> Dict[str, Any]:
    """
    Resilient client caller with exponential backoff and retries
    for transient connection or 5xx errors.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code >= 500:
                    # Retry on server error
                    wait_time = backoff_factor * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exception = e
            wait_time = backoff_factor * (2 ** attempt)
            await asyncio.sleep(wait_time)

    raise RuntimeError(f"Request failed after {max_retries} attempts: {last_exception}")
