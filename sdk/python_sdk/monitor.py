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


import psutil
import asyncio
import time
import aiohttp
from dto import MetricPoint
from auth import AuthProvider


DEFAULT_BUFFER_SIZE = 10
DEFAULT_INTERVAL_SECONDS = 30


class MetricsBuffer:
    """Responsible for buffering and sending metrics"""
    def __init__(self, *, endpoint: str, auth_provider: AuthProvider, buffer_size: int = 10, interval_seconds: int = 30):
        self.endpoint = endpoint
        self.auth_provider = auth_provider
        self.buffer = []
        self.buffer_size = buffer_size
        self.last_flush_time = time.time()
    
    async def add_metric(self, metric: MetricPoint):
        """Add a metric to the buffer and send if buffer is full"""
        self.buffer.append(metric)
        if (len(self.buffer) >= self.buffer_size) or (time.time() - self.last_flush_time >= self.interval_seconds):
            await self.flush()
    
    async def flush(self):
        """Send all buffered metrics"""
        if not self.buffer:
            return
            
        metrics_to_send = self.buffer.copy()
        self.buffer.clear()
        
        try:
            await self._send_metrics(metrics_to_send)
        except Exception as e:
            # Handle error, potentially requeue
            self.buffer = metrics_to_send + self.buffer
            # Implement backoff/retry logic
    
    async def _send_metrics(self, metrics):
        payload = {"metrics": [metric.__dict__ for metric in metrics]}
        
        request_data = {
            'url': self.endpoint,
            'json': payload,
            'headers': {'Content-Type': 'application/json'}
        }
        
        # Apply authentication
        request_data = await self.auth_provider.authenticate(request_data)
        
        # Send request
        async with aiohttp.ClientSession() as session:
            async with session.post(**request_data) as response:
                if response.status >= 400:
                    raise Exception(f"Failed to send metrics: {await response.text()}")

class ResourceMonitor:
    def __init__(self, 
                 *, 
                 service_name: str, 
                 endpoint: str, 
                #  auth_provider: AuthProvider, 
                 buffer_size: int = DEFAULT_BUFFER_SIZE, 
                 interval_seconds: int = DEFAULT_INTERVAL_SECONDS):
        
        self.service_name = service_name
        self.endpoint = endpoint
        # self.auth_provider = auth_provider
        self.running = False
        
        # Dependency injection - pass the sender function to the buffer
        # self.metrics_buffer = MetricsBuffer(
        #     # sender_function=self._send_metrics_batch,
        #     buffer_size=buffer_size,
        #     interval_seconds=interval_seconds
        # )
    
    async def _send_metrics_batch(self, metrics_batch):
        """Implementation of the sender function that the buffer will call"""
        payload = {
            "metrics": [metric.__dict__ for metric in metrics_batch],
            "api_key": self.api_key
        }
        print(payload)
        # Implement actual sending logic here
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(self.endpoint, json=payload) as response:
        #         if response.status >= 400:
        #             raise Exception(f"Failed to send metrics: {await response.text()}")
        
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
    
    async def start_monitoring(self, interval: int = 3):
        self.running = True
        while self.running:
            metric = self._collect_metrics()
            from pprint import pprint
            pprint(metric)
            # await self.metrics_buffer.add(metric)
            await asyncio.sleep(interval)


# Usage
# User configures buffer size and other parameters
monitor = ResourceMonitor(
    service_name="my-service",
    endpoint="localhost:8991/v1/metrics/",
    # api_key="your-api-key",
    buffer_size=20,
    interval_seconds=10
)

# Start monitoring
asyncio.run(monitor.start_monitoring(interval=15))
