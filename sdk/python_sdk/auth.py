from abc import ABC, abstractmethod
import aiohttp
import time


class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, request_data: dict) -> dict:
        """Authenticate and return modified request data with auth details"""
        pass
    
    @abstractmethod
    async def refresh_if_needed(self) -> bool:
        """Refresh authentication if needed, return True if refreshed"""
        pass

class ApiKeyAuth(AuthProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def authenticate(self, request_data: dict) -> dict:
        # Add API key to request data
        if 'headers' not in request_data:
            request_data['headers'] = {}
        request_data['headers']['X-API-Key'] = self.api_key
        return request_data
    
    async def refresh_if_needed(self) -> bool:
        # API keys don't need refreshing
        return False

class OAuth2Auth(AuthProvider):
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.expires_at = 0
    
    async def authenticate(self, request_data: dict) -> dict:
        await self.refresh_if_needed()
        if 'headers' not in request_data:
            request_data['headers'] = {}
        request_data['headers']['Authorization'] = f"Bearer {self.access_token}"
        return request_data
    
    async def refresh_if_needed(self) -> bool:
        current_time = time.time()
        if not self.access_token or current_time >= self.expires_at - 60:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get token: {await response.text()}")
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    self.expires_at = current_time + token_data['expires_in']
                    return True
        return False

class AwsSigV4Auth(AuthProvider):
    def __init__(self, access_key: str, secret_key: str, region: str, service: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service
        # Would use boto3 or similar for actual implementation
    
    async def authenticate(self, request_data: dict) -> dict:
        # Implement AWS SigV4 signing logic
        # This is simplified - real implementation would use boto3 or similar
        # to properly sign the request with AWS SigV4
        return request_data
    
    async def refresh_if_needed(self) -> bool:
        # AWS credentials don't typically need refreshing unless using temporary credentials
        return False