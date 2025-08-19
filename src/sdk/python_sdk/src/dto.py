#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ishmam Hossain <ishmam.dev@gmail.com>
#
# This file is part of CarbonSync.
# CarbonSync is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.
#
# CarbonSync is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# MIT License for more details.
#
# See <https://opensource.org/licenses/MIT>.

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MetricPoint:
    """Represents a single metric point"""
    timestamp: float
    service_name: str
    cpu_usage: float
    memory_usage: float
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    # cloud_region: str
    # instance_type: str
    
@dataclass
class CodeMetrics:
    """Metrics collected from code analysis"""
    complexity: int
    lines_of_code: int
    num_functions: int
    async_functions: int
    memory_patterns: List[str]
    optimization_suggestions: List[str]
    ai_suggestions: str


@dataclass
class LineProfile:
    line_number: int
    source: str
    execution_count: int
    total_time: float
    avg_time: float
    memory_allocated: float  # in MB
    cpu_usage: float  # percentage

@dataclass
class ResourceMetrics:
    peak_memory: float  # in MB
    average_memory: float
    memory_growth: float
    cpu_time: float
    io_operations: int
    network_calls: int
    database_queries: int
    thread_count: int
    gc_collections: Dict[str, int]  # generation-wise collections
    context_switches: int

@dataclass
class PerformanceMetrics:
    line_profiles: List[LineProfile]
    hotspots: List[Dict[str, any]]  # Performance bottlenecks
    resource_usage: ResourceMetrics
    execution_pattern: str  # CPU-bound, IO-bound, Memory-bound
    scalability_score: float  # 0-1 score
    async_efficiency: float  # For async functions
    throughput: float  # operations/second