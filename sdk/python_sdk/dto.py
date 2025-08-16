from dataclasses import dataclass
from typing import Dict


@dataclass
class MetricPoint:
    timestamp: float
    service_name: str
    cpu_usage: float
    memory_usage: float
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    # cloud_region: str
    # instance_type: str