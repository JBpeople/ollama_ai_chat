from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import aiohttp
import asyncio

class ChatAPI(ABC):
    """聊天API接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到服务器"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[Dict]:
        """获取可用模型列表"""
        pass
    
    @abstractmethod
    async def send_message(self, model: str, messages: List[Dict[str, str]]) -> Dict:
        """发送消息"""
        pass

class OllamaChatAPI(ChatAPI):
    """Ollama API实现"""
    
    def __init__(self, base_url: str, timeout: float):
        """
        初始化Ollama API客户端
        
        Args:
            base_url: API的基础URL
            timeout: 请求超时时间（秒）
        """
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'http://{base_url}'
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self) -> None:
        """连接到服务器（创建会话）"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def disconnect(self) -> None:
        """断开连接（关闭会话）"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_models(self) -> List[Dict]:
        """
        获取可用的模型列表
        
        Returns:
            List[Dict]: 模型列表
        
        Raises:
            aiohttp.ClientError: 当API请求失败时
            asyncio.TimeoutError: 当请求超时时
        """
        if not self.session:
            await self.connect()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                response.raise_for_status()
                data = await response.json()
                return data["models"]
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("服务器连接超时，请检查网络或稍后重试")
    
    async def send_message(self, model: str, messages: List[Dict[str, str]]) -> Dict:
        """
        发送聊天请求
        
        Args:
            model: 模型名称
            messages: 消息历史列表
        
        Returns:
            Dict: API响应的消息内容
        
        Raises:
            aiohttp.ClientError: 当API请求失败时
            asyncio.TimeoutError: 当请求超时时
        """
        if not self.session:
            await self.connect()
        
        data = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with self.session.post(f"{self.base_url}/api/chat", json=data) as response:
                response.raise_for_status()
                data = await response.json()
                return data["message"]
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("服务器响应超时，请稍后重试") 