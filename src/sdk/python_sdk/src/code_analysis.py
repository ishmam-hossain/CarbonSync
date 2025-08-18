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

import ast
import inspect
import functools
from typing import List, Callable
from datetime import datetime

from decouple import config

from logger import setup_logger
from dto import CodeMetrics
from producer import initialize_producer
from ai_integration.main import AIOrchestrator

from exceptions import CodeAnalysisError


logger = setup_logger()


send_metrics = initialize_producer(
    broker=config('KAFKA_CODE_ANALYSIS_BROKER', default='localhost:9092'),
    topic=config('KAFKA_CODE_ANALYSIS_TOPIC', default='code_analysis_metrics')
)


class CodeAnalyzer:
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def get_cleaned_code_source_tree(self, func: Callable) -> str:
        # Analyze the function once when decorating
        source = inspect.getsource(func)
        # Remove any indentation to avoid parsing errors
        cleanded_source = inspect.cleandoc(source)
        tree = ast.parse(cleanded_source)
        return cleanded_source, tree
    
    def get_code_metrics(self, func: Callable) -> CodeMetrics:
        """Extract code metrics from the function's AST."""
        _, tree = self.get_cleaned_code_source_tree(func)
        ai_suggestions = self._generate_optimization_suggestions_ai(tree)

        return CodeMetrics(
            complexity=self._calculate_complexity(tree),
            lines_of_code=len(inspect.getsource(func).splitlines()),
            num_functions=sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)),
            async_functions=sum(1 for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)),
            memory_patterns=self._detect_memory_patterns(tree),
            optimization_suggestions=self._generate_suggestions(tree),
            ai_suggestions=ai_suggestions
        )
        
    def __call__(self, func: Callable) -> Callable:
        """Make the class callable as a decorator"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function and measure time
            start_time = datetime.now()
            result = func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            # Send analysis results
            self._send_analysis_results(func.__name__, metrics, execution_time)
            return result
        
        metrics = self.get_code_metrics(func)
        return wrapper
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                               ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
        return complexity
    
    def _detect_memory_patterns(self, tree: ast.AST) -> List[str]:
        """Detect potential memory-intensive patterns"""
        patterns = []
        
        for node in ast.walk(tree):
            # Large list comprehensions
            if isinstance(node, ast.ListComp) and len(node.generators) > 1:
                patterns.append("Complex list comprehension detected - Consider using generator")
            
            # Nested loops
            if isinstance(node, (ast.For, ast.AsyncFor)):
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.AsyncFor)) and child is not node:
                        patterns.append("Nested loop detected - Consider optimization")
        
        return patterns
    
    def _generate_suggestions(self, tree: ast.AST) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        for node in ast.walk(tree):
            # Check for large string operations
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Str) or isinstance(node.right, ast.Str):
                    suggestions.append("String concatenation in loop - Consider using join()")
            
            # Check for repeated function calls
            if isinstance(node, ast.Call):
                suggestions.append(f"Consider caching result of function call: {ast.unparse(node)}")
        
        return suggestions
    
    def _generate_optimization_suggestions_ai(self, tree: ast.AST) -> str:
        """Get AI-generated suggestions for code improvements"""
        orchestrator = AIOrchestrator()
        result = orchestrator.analyze_code_tree(tree)
        return result
    
    def _send_analysis_results(self, function_name: str, metrics: CodeMetrics, execution_time: float) -> None:
        """Send analysis results to Kafka"""
        payload = {
            "service_name": self.service_name,
            "function_name": function_name,
            "timestamp": datetime.now().timestamp(),
            "execution_time": execution_time,
            "metrics": {
                "complexity": metrics.complexity,
                "lines_of_code": metrics.lines_of_code,
                "num_functions": metrics.num_functions,
                "async_functions": metrics.async_functions,
                "memory_patterns": metrics.memory_patterns,
                "optimization_suggestions": metrics.optimization_suggestions,
                "ai_suggestions": metrics.ai_suggestions
            }
        }
        
        # Send to Kafka topic
        send_metrics(message=payload)


code_analyzer = CodeAnalyzer(service_name=config("SERVICE_NAME", default="code_analyzer_service"))

# Example usage

if __name__ == "__main__":
    import asyncio
    
    analyzer = CodeAnalyzer(service_name="example_service")

    @analyzer
    async def example_function():
        # Example of inefficient code
        data = [i * 2 for i in range(1000)]
        result = ""
        for item in data:
            result += str(item)
        return result
    
    async def main():
        result = await example_function()
        print(f"Function result: {result}")
    
    asyncio.run(main())