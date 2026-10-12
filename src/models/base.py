"""
Core abstractions and interfaces for forecasting models and registries.
Adheres to SOLID Principles:
- Single Responsibility: Specialized interfaces for predicting, training, and versioning.
- Open/Closed: Extensible forecaster and registry hierarchy.
- Liskov Substitution: Any forecaster adhering to IForecaster can be substituted.
- Interface Segregation: Discrete IForecaster, ITrainable, and IVersionable interfaces.
- Dependency Inversion: High-level serving and pipelines depend on IForecaster / IModelRegistry.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Type
import numpy as np
import pandas as pd

class IForecaster(ABC):
    """
    Interface Segregation: Base prediction contract.
    Guarantees Liskov Substitution Principle across all baseline and ML forecasters.
    """
    @abstractmethod
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Generates demand forecast predictions for the input feature DataFrame."""
        pass

class ITrainable(ABC):
    """
    Interface Segregation: Model training contract.
    """
    @abstractmethod
    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        **kwargs: Any
    ) -> "ITrainable":
        """Fits model parameters using training and optional validation sets."""
        pass

class IVersionable(ABC):
    """
    Interface Segregation: Model serialization and introspection contract.
    """
    @abstractmethod
    def save(self, model_dir: Path) -> None:
        """Serializes model artifacts and metadata to disk."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, model_dir: Path) -> "IVersionable":
        """Deserializes model artifacts and metadata from disk."""
        pass

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Returns normalized feature importance dictionary."""
        pass

class IModelRegistry(ABC):
    """
    Dependency Inversion: Abstract registry contract for model versioning and rollback.
    """
    @abstractmethod
    def register(
        self,
        version: str,
        forecaster: Any,
        metrics: Dict[str, Any],
        description: str = "",
        promote: bool = False
    ) -> Dict[str, Any]:
        """Registers a new candidate model in the registry."""
        pass

    @abstractmethod
    def get_champion(self) -> Tuple[str, Any]:
        """Retrieves active champion version ID and loaded forecaster instance."""
        pass

    @abstractmethod
    def rollback(self) -> Tuple[str, str]:
        """Performs atomic pointer rollback to previous active champion."""
        pass

    @abstractmethod
    def list_versions(self) -> List[Dict[str, Any]]:
        """Lists all registered models with their metadata and promotion statuses."""
        pass

class ForecasterFactory:
    """
    Factory Pattern: Creates forecaster instances by algorithm identifier.
    Open/Closed Principle: New forecasters register dynamically without altering callers.
    """
    _registry: Dict[str, Type[IForecaster]] = {}

    @classmethod
    def register_algorithm(cls, name: str, forecaster_cls: Type[IForecaster]) -> None:
        """Registers a forecaster class under a unique algorithm identifier."""
        cls._registry[name.lower()] = forecaster_cls

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> IForecaster:
        """Instantiates a registered forecaster."""
        name_lower = name.lower()
        if name_lower not in cls._registry:
            raise ValueError(f"Unknown forecaster algorithm '{name}'. Available: {list(cls._registry.keys())}")
        return cls._registry[name_lower](**kwargs)
