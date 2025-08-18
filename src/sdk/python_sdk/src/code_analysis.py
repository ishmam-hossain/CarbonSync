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

import functools
import asyncio
from typing import Callable, Any, Optional

from monitor import ResourceMonitor

def carbon_track(
    service_name: str,
    buffer_size: int = 10,
    flush_interval_seconds: int = 30,
    collection_interval_seconds: int = 3
) -> Callable:
    """
    Decorator to track carbon metrics for async functions.
    
    Args:
        service_name: Name of the service being monitored
        buffer_size: Number of metrics to buffer before sending
        flush_interval_seconds: Maximum time to wait before sending metrics
        collection_interval_seconds: Interval between metric collections
    """
    def decorator(func: Callable) -> Callable:
        monitor = ResourceMonitor(
            service_name=service_name,
            buffer_size=buffer_size,
            flush_interval_seconds=flush_interval_seconds
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Start monitoring in background task
            monitor_task = asyncio.create_task(
                monitor.start_monitoring(
                    collection_interval_seconds=collection_interval_seconds
                )
            )
            
            try:
                # Execute the decorated function
                result = await func(*args, **kwargs)
                return result
            finally:
                # Stop monitoring and ensure metrics are flushed
                monitor.running = False
                await monitor.metrics_buffer.flush()
                await monitor_task
        
        return wrapper
    return decorator



if __name__ == "__main__":
    # Example usage
    @carbon_track(service_name="example_service", buffer_size=5, flush_interval_seconds=10)
    async def example_function():
        await asyncio.sleep(1)
        return "Function executed"

    # Run the example function
    asyncio.run(example_function())