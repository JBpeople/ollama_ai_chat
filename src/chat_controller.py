from typing import List, Dict, Optional
from config_manager import ConfigManager
from chat_api import ChatAPI

class ChatController:
    """聊天控制器，处理业务逻辑"""
    
    def __init__(self, config_manager: ConfigManager, chat_api: ChatAPI):
        self.config_manager = config_manager
        self.chat_api = chat_api
        self.messages: List[Dict[str, str]] = []
        self.is_connected = False
        self.current_model: Optional[str] = None
    
    def initialize(self):
        """初始化配置"""
        self.config_manager.load_config()
    
    async def connect(self, server_url: str) -> List[Dict]:
        """连接到服务器"""
        try:
            self.chat_api = type(self.chat_api)(
                server_url,
                self.config_manager.get_timeout()
            )
            models = await self.chat_api.get_models()
            self.is_connected = True
            self.config_manager.set_server_url(server_url)
            return models
        except Exception as e:
            self.is_connected = False
            raise e
    
    async def disconnect(self):
        """断开连接"""
        if self.chat_api:
            await self.chat_api.disconnect()
        self.is_connected = False
        self.current_model = None
        self.messages.clear()
    
    async def send_message(self, message: str) -> Dict:
        """发送消息"""
        if not self.is_connected or not self.current_model:
            raise RuntimeError("未连接到服务器或未选择模型")
        
        self.messages.append({"role": "user", "content": message})
        try:
            response = await self.chat_api.send_message(
                self.current_model,
                self.messages
            )
            self.messages.append(response)
            return response
        except Exception as e:
            self.messages.pop()  # 移除未成功的消息
            raise e
    
    def set_current_model(self, model: str):
        """设置当前模型"""
        self.current_model = model
    
    def toggle_favorite(self, server_url: str) -> bool:
        """切换收藏状态"""
        favorites = self.config_manager.get_favorite_servers()
        if server_url in favorites:
            self.config_manager.remove_favorite_server(server_url)
            return False
        else:
            self.config_manager.add_favorite_server(server_url)
            return True
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取消息历史"""
        return self.messages.copy()
    
    def get_favorite_servers(self) -> List[str]:
        """获取收藏的服务器列表"""
        return self.config_manager.get_favorite_servers()
    
    def is_favorite(self, server_url: str) -> bool:
        """检查服务器是否已收藏"""
        return server_url in self.config_manager.get_favorite_servers() 