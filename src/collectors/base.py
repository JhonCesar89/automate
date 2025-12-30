"""
Base collector class that all system collectors inherit from.
Provides common interface and utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class ServiceData:
    """Standardized service data structure across all systems."""
    
    # Identifiers
    service_id: str
    engineering_id: Optional[str] = None
    order_number: Optional[str] = None
    
    # Client info
    client_name: Optional[str] = None
    client_site: Optional[str] = None
    
    # Network - LAN side
    lan_ip: Optional[str] = None
    lan_network: Optional[str] = None
    lan_mask: Optional[str] = None
    bandwidth: Optional[int] = None  # in kbps
    
    # Network - CPE
    cpe_name: Optional[str] = None
    cpe_model: Optional[str] = None
    cpe_management_ip: Optional[str] = None
    cpe_management_vlan: Optional[int] = None
    cpe_interface_vlan: Optional[int] = None
    cpe_wan_ip: Optional[str] = None
    cpe_port: Optional[str] = None
    
    # Network - Aggregation
    ring_name: Optional[str] = None  # ME-XXXX_XXXX
    aggregator_name: Optional[str] = None
    aggregator_port_1: Optional[str] = None
    aggregator_port_2: Optional[str] = None
    bvi_vlan: Optional[int] = None
    wan_aggi_ip: Optional[str] = None
    wan_mask: Optional[str] = None
    
    # Status
    status: Optional[str] = None
    status_date: Optional[datetime] = None
    
    # Metadata
    source_system: str = ""
    collected_at: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base class for all system collectors."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self._connected = False
        logger.info(f"Initializing {self.name}")
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the system."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the system."""
        pass
    
    @abstractmethod
    def search_by_service(self, service_id: str) -> Optional[ServiceData]:
        """Search for a specific service by ID."""
        pass
    
    @abstractmethod
    def search_by_ring(self, ring_name: str) -> List[ServiceData]:
        """Get all services in a specific ring."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if collector is connected."""
        return self._connected
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
