from abc import ABC, abstractmethod
import configparser
import json
import os
from typing import List

class ConfigManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def load_config(self) -> None:
        """加载配置"""
        pass
    
    @abstractmethod
    def save_config(self) -> None:
        """保存配置"""
        pass
    
    @abstractmethod
    def get_server_url(self) -> str:
        """获取服务器地址"""
        pass
    
    @abstractmethod
    def set_server_url(self, url: str) -> None:
        """设置服务器地址"""
        pass
    
    @abstractmethod
    def get_timeout(self) -> float:
        """获取超时设置"""
        pass
    
    @abstractmethod
    def set_timeout(self, timeout: float) -> None:
        """设置超时时间"""
        pass
    
    @abstractmethod
    def get_favorite_servers(self) -> List[str]:
        """获取收藏的服务器列表"""
        pass
    
    @abstractmethod
    def add_favorite_server(self, url: str) -> None:
        """添加收藏服务器"""
        pass
    
    @abstractmethod
    def remove_favorite_server(self, url: str) -> None:
        """移除收藏服务器"""
        pass
    
    @abstractmethod
    def get_close_action(self) -> str:
        """获取关闭行为设置"""
        pass
    
    @abstractmethod
    def set_close_action(self, action: str) -> None:
        """设置关闭行为"""
        pass

class IniConfigManager(ConfigManager):
    """INI文件配置管理器实现"""
    
    def __init__(self, config_file: str, default_server: str, default_timeout: float):
        self.config_file = config_file
        self.default_server = default_server
        self.default_timeout = default_timeout
        self.config = configparser.ConfigParser()
        self.server_url = default_server
        self.timeout = default_timeout
        self.favorite_servers: List[str] = []
        self.close_action = "ask"  # 默认询问
    
    def load_config(self) -> None:
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding="utf-8")
                
                if self.config.has_section("Server"):
                    self.server_url = self.config.get("Server", "url", fallback=self.default_server)
                
                if self.config.has_section("Chat"):
                    self.timeout = self.config.getfloat("Chat", "timeout", fallback=self.default_timeout)
                
                if self.config.has_section("Favorites"):
                    favorites_str = self.config.get("Favorites", "servers", fallback="[]")
                    self.favorite_servers = json.loads(favorites_str)
                
                if self.config.has_section("Window"):
                    self.close_action = self.config.get("Window", "close_action", fallback="ask")
            else:
                self._create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def save_config(self) -> None:
        try:
            self._ensure_sections()
            
            self.config["Server"]["url"] = self.server_url
            self.config["Chat"]["timeout"] = str(self.timeout)
            self.config["Favorites"]["servers"] = json.dumps(self.favorite_servers)
            self.config["Window"]["close_action"] = self.close_action
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_server_url(self) -> str:
        return self.server_url
    
    def set_server_url(self, url: str) -> None:
        self.server_url = url
        self.save_config()
    
    def get_timeout(self) -> float:
        return self.timeout
    
    def set_timeout(self, timeout: float) -> None:
        self.timeout = timeout
        self.save_config()
    
    def get_favorite_servers(self) -> List[str]:
        return self.favorite_servers.copy()
    
    def add_favorite_server(self, url: str) -> None:
        if url not in self.favorite_servers:
            self.favorite_servers.append(url)
            self.save_config()
    
    def remove_favorite_server(self, url: str) -> None:
        if url in self.favorite_servers:
            self.favorite_servers.remove(url)
            self.save_config()
    
    def get_close_action(self) -> str:
        return self.close_action
    
    def set_close_action(self, action: str) -> None:
        self.close_action = action
        self.save_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        self.server_url = self.default_server
        self.timeout = self.default_timeout
        self.favorite_servers = []
        self.close_action = "ask"
        self.save_config()
    
    def _ensure_sections(self) -> None:
        """确保所有必要的配置节点存在"""
        for section in ["Server", "Chat", "Favorites", "Window"]:
            if not self.config.has_section(section):
                self.config.add_section(section) 