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

import time
import asyncio

import psutil
from decouple import config

from dto import MetricPoint
from producer import dump_metrics


DEFAULT_BUFFER_SIZE = config('DEFAULT_BUFFER_SIZE', default=10, cast=int)
DEFAULT_FLUSH_INTERVAL_SECONDS = config('DEFAULT_FLUSH_INTERVAL_SECONDS', default=30, cast=int)
DEFAULT_COLLECTION_INTERVAL_SECONDS = config('DEFAULT_COLLECTION_INTERVAL_SECONDS', default=3, cast=int)


class MetricsBuffer:
    """Responsible for buffering and sending metrics"""
    def __init__(self, 
                    *, 
                    buffer_size: int = 10, 
                    flush_interval_seconds: int = 30):
        self.buffer = []
        self.buffer_size = buffer_size
        self.flush_interval_seconds = flush_interval_seconds
        self.last_flush_time = time.time()
    
    async def append(self, metric: MetricPoint):
        """Add a metric to the buffer and send if buffer is full"""
        self.buffer.append(metric)
        if (len(self.buffer) >= self.buffer_size) or (time.time() - self.last_flush_time >= self.flush_interval_seconds):
            await self.flush()

    async def flush(self):
        """Send all buffered metrics"""
        if not self.buffer:
            return
            
        metrics_to_send = self.buffer.copy()
        self.buffer.clear()
        
        await self._send_metrics(metrics_to_send)
    
    async def _send_metrics(self, metrics):
        payload = {"metrics": [metric.__dict__ for metric in metrics]}
        dump_metrics(message=payload)


class ResourceMonitor:
    def __init__(self, 
                    *, 
                    service_name: str, 
                    endpoint: str, 
                    buffer_size: int = DEFAULT_BUFFER_SIZE,
                    flush_interval_seconds: int = DEFAULT_FLUSH_INTERVAL_SECONDS):
        
        self.running = False
        self.service_name = service_name
        self.metrics_buffer = self.get_buffer_instance(endpoint=endpoint,
                                                        buffer_size=buffer_size, 
                                                        flush_interval_seconds=flush_interval_seconds)
        
    def get_buffer_instance(self, 
                            *, 
                            endpoint: str, 
                            buffer_size: int, 
                            flush_interval_seconds: int):
        
        return MetricsBuffer(
            endpoint=endpoint,
            buffer_size=buffer_size,
            flush_interval_seconds=flush_interval_seconds
        )

    def _collect_metrics(self) -> MetricPoint:
        """Collect system metrics"""
        return MetricPoint(
            timestamp=time.time(),
            service_name=self.service_name,
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            network_io=psutil.net_io_counters()._asdict(),
            disk_io=psutil.disk_io_counters()._asdict(),
            # cloud_region=self._detect_cloud_region(),
            # instance_type=self._detect_instance_type()
        )
    
    async def start_monitoring(self, collection_interval_seconds: int = 3):
        self.running = True
        while self.running:
            metric = self._collect_metrics()
            await self.metrics_buffer.append(metric)
            await asyncio.sleep(collection_interval_seconds)


# Usage
# User configures buffer size and other parameters
monitor = ResourceMonitor(
    service_name="my-service",
    buffer_size=20,
    flush_interval_seconds=5
)

# Start monitoring
asyncio.run(monitor.start_monitoring(collection_interval_seconds=3))
