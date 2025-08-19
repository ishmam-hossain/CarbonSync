from typing import Dict, Type, Optional
from abc import ABC, abstractmethod
import ast
import json
from enum import Enum
from decouple import config

from producer import initialize_producer

from logger import setup_logger
logger = setup_logger()


send_metrics = initialize_producer(
    broker=config('KAFKA_AI_BROKER', default='localhost:9092'),
    topic=config('KAFKA_AI_TOPIC', default='ai_code_analysis_metrics')
)


class AIProvider(Enum):
    OLLAMA = "ollama"
    BEDROCK = "bedrock"
    # Add more providers as needed

class AIServiceHandler(ABC):
    @abstractmethod
    async def analyze_code(self, tree: ast.AST) -> Dict[str, any]:
        """Analyze code and return optimization suggestions"""
        pass

    @abstractmethod
    async def get_optimization_strategy(self, analysis_result: Dict) -> str:
        """Generate optimization strategy based on analysis"""
        pass

class AIOrchestrator:
    def __init__(self):
        self.provider = self._get_ai_provider()
        self.handler = self._initialize_handler()

    def _get_ai_provider(self) -> AIProvider:
        """Get AI provider from environment variables"""
        provider_name = config('AI_PROVIDER', default='ollama').lower()
        try:
            return AIProvider(provider_name)
        except ValueError:
            raise ValueError(f"Unsupported AI provider: {provider_name}")

    def _initialize_handler(self) -> AIServiceHandler:
        """Initialize the appropriate AI service handler"""
        handlers: Dict[AIProvider, Type[AIServiceHandler]] = {
            AIProvider.OLLAMA: self._import_handler("ollama_handler", "OllamaHandler"),
            # AIProvider.BEDROCK: self._import_handler("bedrock_handler", "BedrockHandler"),
        }
        
        handler_class = handlers.get(self.provider)
        if not handler_class:
            raise ValueError(f"No handler found for provider: {self.provider}")
        
        return handler_class()

    def _import_handler(self, module_name: str, class_name: str) -> Type[AIServiceHandler]:
        """Dynamically import handler class"""
        try:
            module = __import__(f"ai_integration.handlers.{module_name}", fromlist=[class_name])
            return getattr(module, class_name)
        except ImportError as e:
            raise ImportError(f"Failed to import {class_name} from {module_name}: {e}")

    def analyze_code_tree(self, tree: ast.AST) -> Dict[str, any]:
        """Analyze code tree and generate optimization suggestions"""
        try:
            analysis_result = self.handler.analyze_code(tree)
            optimization_strategy = self.handler.get_optimization_strategy(analysis_result)
            
            return {
                "provider": self.provider.value,
                "analysis": analysis_result,
                "optimization_strategy": optimization_strategy
            }
        except Exception as e:
            raise RuntimeError(f"AI analysis failed: {str(e)}")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def example():
        code = """
        def process_data():
            result = []
            for i in range(1000):
                result.append(str(i))
            return ''.join(result)
        """
        
        tree = ast.parse(code)
        orchestrator = AIOrchestrator()
        result = await orchestrator.analyze_code_tree(tree)
        print(json.dumps(result, indent=2))
    
    asyncio.run(example())