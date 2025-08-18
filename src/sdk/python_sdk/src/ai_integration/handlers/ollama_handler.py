import ast
from typing import Dict
import httpx
from decouple import config

from ollama import chat
from ollama import ChatResponse

from ..main import AIServiceHandler

class OllamaHandler(AIServiceHandler):
    def __init__(self):
        self.base_url = config('OLLAMA_API_URL', default='http://localhost:11434')
        self.model = config('OLLAMA_MODEL', default='codellama')
        self.client = httpx.AsyncClient()

    def analyze_code(self, tree: ast.AST) -> Dict[str, any]:
        """Analyze code using Ollama"""
        code_str = ast.unparse(tree)
        
        prompt = f"""
        Analyze this Python code for performance and resource usage:
        
        {code_str}
        
        Focus on:
        1. CPU efficiency
        2. Memory usage
        3. I/O operations
        4. Algorithm complexity
        
        Return the analysis as JSON with these categories.
        """
        
        # response = await self.client.post(
        #     f"{self.base_url}/api/generate",
        #     json={
        #         "model": self.model,
        #         "prompt": prompt,
        #         "format": "json"
        #     }
        # )
        

        response: ChatResponse = chat(model='codellama', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])        
        return response.json()

    def get_optimization_strategy(self, analysis_result: Dict) -> str:
        """Generate optimization strategy based on analysis"""
        prompt = f"""
        Based on this code analysis:
        {analysis_result}
        
        Suggest concrete optimization strategies to reduce:
        1. CPU usage
        2. Memory consumption
        3. Carbon footprint
        
        Provide specific code examples where applicable.
        """
        
        # response = await self.client.post(
        #     f"{self.base_url}/api/generate",
        #     json={
        #         "model": self.model,
        #         "prompt": prompt
        #     }
        # )
        
        response: ChatResponse = chat(model='codellama', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ]) 
        
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.client.close()