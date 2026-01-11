"""
配置管理模組
"""
import yaml
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str):
        """
        初始化配置管理器
        
        Args:
            config_path: 設定檔路徑
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加載配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        """
        獲取配置值（支持點號分隔的多級鍵）
        
        Args:
            key: 配置鍵，如 "game.window_title"
            default: 預設值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def reload(self):
        """重新加載配置文件"""
        self.config = self._load_config()
