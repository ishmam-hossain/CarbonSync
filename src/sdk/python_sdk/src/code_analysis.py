import asyncio
import inspect
import functools
import time
import psutil
from typing import Any, Dict, Callable
from datetime import datetime
from line_profiler import LineProfiler
from decouple import config

from producer import initialize_producer
from logger import setup_logger

logger = setup_logger()


async def get_kafka_producer():
    return await initialize_producer(
        broker=config('KAFKA_CODE_ANALYSIS_BROKER', default='localhost:9092'),
        topic=config('KAFKA_CODE_ANALYSIS_TOPIC', default='performance_metrics')
    )

send_metrics = asyncio.run(get_kafka_producer())


class CodeAnalyzer:
    """Simple code analyzer that tracks execution time and resource usage."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.process = psutil.Process()
        self.line_profiler = LineProfiler()

    def __call__(self, func: Callable) -> Callable:
        """Decorator to analyze function performance."""
        self.line_profiler.add_function(func)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Capture start metrics
            start_time = time.perf_counter()
            start_memory = self.process.memory_info().rss # Bytes
            
            try:
                # Execute function
                result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Capture end metrics
                execution_time = time.perf_counter() - start_time
                memory_used = self.process.memory_info().rss - start_memory
                
                # Get line profiling data
                self.line_profiler.enable()
                self.line_profiler.disable()
                stats = self.line_profiler.get_stats()

                # Prepare metrics
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'function_name': func.__name__,
                    'service_name': self.service_name,
                    'execution_time': execution_time,
                    'memory_used_mb': memory_used,
                    'cpu_percent': self.process.cpu_percent(),
                    'line_profiles': self._get_line_stats(stats)
                }
                
                # Send metrics to Kafka
                asyncio.create_task(self._send_metrics(metrics))
                
                return result
                
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
                
        return wrapper
    
    def _get_line_stats(self, stats: Any) -> Dict:
        """Extract simplified line profiling statistics."""
        line_stats: Dict[str, Dict] = {}
        for (filename, line_no, func_name), timings in stats.timings.items():
            line_stats[filename] = {}
            for line_no, hits, total_time in timings:
                line_stats[line_no] = {
                    'hits': hits,
                    'total_time': total_time * stats.unit,  # Convert to seconds
                    'avg_time': (total_time * stats.unit) / hits if hits > 0 else 0
                }
        return line_stats
    
    async def _send_metrics(self, metrics: Dict) -> None:
        """Send metrics to Kafka."""
        try:
            await send_metrics(message=metrics)
        except Exception as e:
            logger.error(f"Failed to send metrics: {str(e)}")


analyzer = CodeAnalyzer(service_name=config('SERVICE_NAME', default="code_analyzer_service"))



# Example usage
# if __name__ == "__main__":

#     @analyzer
#     async def example_function(n: int):
#         result = []
#         for i in range(n):
#             result.append(str(i))
#         return ''.join(result)

#     async def main():
#         try:
#             result = await example_function(1000)
#             print(f"Function completed with result length: {len(result)}")
#         except Exception as e:
#             logger.error(f"Main execution error: {str(e)}")

#     asyncio.run(main())e