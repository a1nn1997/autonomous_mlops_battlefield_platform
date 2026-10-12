import pandas as pd
from typing import Tuple, Dict, Any
from src.config import settings

class TimeBasedSplitter:
    """
    Partitions time-series data using temporal boundaries to prevent lookahead bias.
    """

    def __init__(
        self,
        train_end: str = settings.data.train_end_date,
        val_end: str = settings.data.val_end_date,
        test_end: str = settings.data.test_end_date,
        date_col: str = settings.data.date_col
    ):
        self.train_end = pd.to_datetime(train_end)
        self.val_end = pd.to_datetime(val_end)
        self.test_end = pd.to_datetime(test_end)
        self.date_col = date_col

    def split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits df into (train, val, test) partitions.
        Guarantees:
          train.date <= train_end
          train_end < val.date <= val_end
          val_end < test.date <= test_end
        """
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[self.date_col]):
            df[self.date_col] = pd.to_datetime(df[self.date_col])

        train_mask = df[self.date_col] <= self.train_end
        val_mask = (df[self.date_col] > self.train_end) & (df[self.date_col] <= self.val_end)
        test_mask = (df[self.date_col] > self.val_end) & (df[self.date_col] <= self.test_end)

        train_df = df[train_mask].copy().reset_index(drop=True)
        val_df = df[val_mask].copy().reset_index(drop=True)
        test_df = df[test_mask].copy().reset_index(drop=True)

        return train_df, val_df, test_df

    def get_summary(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "train": {
                "rows": len(train_df),
                "min_date": train_df[self.date_col].min().strftime("%Y-%m-%d"),
                "max_date": train_df[self.date_col].max().strftime("%Y-%m-%d"),
            },
            "validation": {
                "rows": len(val_df),
                "min_date": val_df[self.date_col].min().strftime("%Y-%m-%d"),
                "max_date": val_df[self.date_col].max().strftime("%Y-%m-%d"),
            },
            "test": {
                "rows": len(test_df),
                "min_date": test_df[self.date_col].min().strftime("%Y-%m-%d"),
                "max_date": test_df[self.date_col].max().strftime("%Y-%m-%d"),
            }
        }
