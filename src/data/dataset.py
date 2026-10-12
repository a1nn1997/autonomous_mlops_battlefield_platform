import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
from src.config import settings, DATA_DIR

def generate_retail_data(
    start_date: str = settings.data.start_date,
    end_date: str = settings.data.end_date,
    n_items: int = settings.data.n_items,
    n_stores: int = settings.data.n_stores,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic M5-compatible multi-entity retail demand dataset.
    Features:
      - Hierarchical items & departments (FOODS, HOUSEHOLD) across stores
      - Strong day-of-week seasonality (weekend shopping surges)
      - Annual seasonal fluctuations (holiday cycles)
      - Price elasticity: demand responds negatively to price hikes
      - Promotional lifts: 40-100% demand surge during active promotions
      - Realistic calendar events (SuperBowl, MemorialDay, Thanksgiving, Christmas)
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(date_range)

    store_ids = [f"STORE_{i+1:02d}" for i in range(n_stores)]
    dept_names = ["FOODS_1", "FOODS_2", "HOUSEHOLD_1"]
    items = []
    for i in range(n_items):
        dept = dept_names[i % len(dept_names)]
        items.append((f"ITEM_{i+1:03d}", dept))

    records: List[dict] = []

    # Store base multipliers
    store_factors = {s: 0.8 + 0.4 * idx / max(1, n_stores - 1) for idx, s in enumerate(store_ids)}
    
    # Item base characteristics
    item_params = {}
    for item_id, dept in items:
        base_demand = np.random.uniform(15, 60)
        base_price = np.random.uniform(2.5, 12.0)
        price_elasticity = np.random.uniform(-1.5, -0.6)
        item_params[item_id] = {
            "dept": dept,
            "base_demand": base_demand,
            "base_price": base_price,
            "elasticity": price_elasticity
        }

    for store_id in store_ids:
        store_mult = store_factors[store_id]
        for item_id, dept in items:
            params = item_params[item_id]
            base_sales = params["base_demand"] * store_mult
            base_price = params["base_price"]
            elasticity = params["elasticity"]

            for dt in date_range:
                day_of_week = dt.dayofweek
                day_of_year = dt.dayofyear
                is_weekend = 1 if day_of_week in [5, 6] else 0

                # 1. Day of week seasonal multiplier (Saturday/Sunday peak)
                dow_mult = 1.0 + 0.35 * (day_of_week >= 5) + 0.15 * (day_of_week == 4) - 0.1 * (day_of_week in [1, 2])
                
                # 2. Annual seasonality (sinusoidal)
                annual_mult = 1.0 + 0.18 * np.sin(2 * np.pi * day_of_year / 365.25)

                # 3. Calendar events
                is_event = 0
                event_mult = 1.0
                if (dt.month == 11 and dt.day >= 24 and dt.day <= 28): # Thanksgiving / Black Friday
                    is_event = 1
                    event_mult = 1.7
                elif (dt.month == 12 and dt.day >= 20 and dt.day <= 24): # Christmas week
                    is_event = 1
                    event_mult = 1.85
                elif (dt.month == 12 and dt.day == 25): # Christmas Day store closed
                    is_event = 1
                    event_mult = 0.05
                elif (dt.month == 7 and dt.day == 4): # 4th July
                    is_event = 1
                    event_mult = 1.4

                # 4. Promotions (random promotional campaigns)
                # Approximately 15% probability of promo
                is_promo = 1 if (np.random.rand() < 0.15) else 0
                promo_mult = np.random.uniform(1.4, 2.0) if is_promo else 1.0
                
                # 5. Price variation: discounts on promo, minor drift otherwise
                discount = np.random.uniform(0.15, 0.30) if is_promo else 0.0
                sell_price = round(max(0.99, base_price * (1.0 - discount) + np.random.normal(0, 0.05)), 2)

                # Price effect
                price_ratio = sell_price / base_price
                price_mult = (price_ratio ** elasticity)

                # Combined expected demand
                expected_sales = base_sales * dow_mult * annual_mult * event_mult * promo_mult * price_mult
                expected_sales = max(0.0, expected_sales)

                # Poisson / negative-binomial like stochastic realization
                actual_sales = np.random.poisson(lam=expected_sales)

                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "store_id": store_id,
                    "item_id": item_id,
                    "dept_id": dept,
                    "sell_price": sell_price,
                    "is_promo": is_promo,
                    "is_event": is_event,
                    "is_weekend": is_weekend,
                    "sales": int(actual_sales)
                })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["store_id", "item_id", "date"]).reset_index(drop=True)
    return df

class RetailDemandDataset:
    """Dataset manager for loading or synthesizing retail sales time-series."""
    
    def __init__(self, raw_path: Optional[Path] = None):
        self.raw_path = raw_path or (DATA_DIR / "raw" / "retail_sales.csv")

    def load_or_generate(self, force_generate: bool = False) -> pd.DataFrame:
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        if self.raw_path.exists() and not force_generate:
            df = pd.read_csv(self.raw_path)
            df["date"] = pd.to_datetime(df["date"])
            return df
        
        df = generate_retail_data()
        df.to_csv(self.raw_path, index=False)
        return df

    def load_m5_subset(self, m5_path: Optional[Path] = None, max_items: int = 10, max_stores: int = 4) -> pd.DataFrame:
        """
        Loads an authentic M5 competition subset if available on disk;
        otherwise generates a synthetic M5-style retail demand dataset using seeded generator.
        """
        target = m5_path or (DATA_DIR / "raw" / "m5_sample.csv")
        if target.exists():
            df = pd.read_csv(target)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
        return generate_retail_data(n_items=max_items, n_stores=max_stores)

def load_m5_subset(m5_path: Optional[Path] = None, max_items: int = 10, max_stores: int = 4) -> pd.DataFrame:
    """Convenience helper to load M5 subset or synthetic M5-style retail demand."""
    return RetailDemandDataset().load_m5_subset(m5_path=m5_path, max_items=max_items, max_stores=max_stores)
