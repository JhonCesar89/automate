"""Data collectors for various systems."""
from .base import BaseCollector, ServiceData
from .wid_collector import WIDCollector, get_service_from_wid

__all__ = [
    "BaseCollector",
    "ServiceData", 
    "WIDCollector",
    "get_service_from_wid",
]
