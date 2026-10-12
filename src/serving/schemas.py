from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "healthy"
    model_version: Optional[str] = None
    uptime_seconds: float = 0.0
    timestamp: str

class ForecastItem(BaseModel):
    store_id: str = Field(..., json_schema_extra={"example": "STORE_01"})
    item_id: str = Field(..., json_schema_extra={"example": "ITEM_001"})
    dept_id: str = Field("FOODS_1", json_schema_extra={"example": "FOODS_1"})
    sell_price: float = Field(..., json_schema_extra={"example": 3.99})
    is_promo: int = Field(0, json_schema_extra={"example": 1})
    is_event: int = Field(0, json_schema_extra={"example": 0})
    is_weekend: int = Field(0, json_schema_extra={"example": 0})
    day_of_week: int = Field(2, json_schema_extra={"example": 2})
    day_of_month: int = Field(15, json_schema_extra={"example": 15})
    month: int = Field(6, json_schema_extra={"example": 6})
    year: int = Field(2024, json_schema_extra={"example": 2024})
    lag_1: float = Field(..., json_schema_extra={"example": 25.0})
    lag_7: float = Field(..., json_schema_extra={"example": 28.0})
    lag_14: float = Field(..., json_schema_extra={"example": 24.0})
    lag_28: float = Field(..., json_schema_extra={"example": 26.0})
    rolling_mean_7: float = Field(..., json_schema_extra={"example": 25.5})
    rolling_std_7: float = Field(2.1, json_schema_extra={"example": 2.1})
    rolling_mean_14: float = Field(..., json_schema_extra={"example": 25.2})
    rolling_std_14: float = Field(2.3, json_schema_extra={"example": 2.3})
    rolling_mean_28: float = Field(..., json_schema_extra={"example": 25.0})
    rolling_std_28: float = Field(2.5, json_schema_extra={"example": 2.5})
    price_ratio_28: float = Field(1.0, json_schema_extra={"example": 0.9})
    price_diff_7: float = Field(0.0, json_schema_extra={"example": -0.5})
    dow_sin: float = Field(0.0, json_schema_extra={"example": 0.78})
    dow_cos: float = Field(1.0, json_schema_extra={"example": 0.62})
    month_sin: float = Field(0.0, json_schema_extra={"example": 0.5})
    month_cos: float = Field(1.0, json_schema_extra={"example": 0.86})

class PredictionRequest(BaseModel):
    items: List[ForecastItem]

class ItemPrediction(BaseModel):
    store_id: str
    item_id: str
    predicted_sales: float

class PredictionResponse(BaseModel):
    model_version: str
    predictions: List[ItemPrediction]
    count: int
    latency_ms: float

class RollbackResponse(BaseModel):
    status: str
    active_version: str
    previous_version: str
    message: str

class ModelListResponse(BaseModel):
    active_version: Optional[str]
    models: List[Dict[str, Any]]
