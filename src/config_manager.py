"""
配置管理模組
"""

import sys
from pathlib import Path

import yaml


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        """
        初始化配置管理器

        Args:
            config_path: 設定檔路徑
        """
        # 處理 PyInstaller 打包後的路徑
        if getattr(sys, "frozen", False):
            # 打包後，優先使用 exe 所在目錄的外部配置
            external_path = Path(sys.executable).parent / config_path
            if external_path.exists():
                self.config_path = external_path
            else:
                # 如果外部不存在，使用打包內的配置
                internal_path = (
                    Path(getattr(sys, "_MEIPASS", "")) / config_path
                )
                self.config_path = internal_path
        else:
            # 開發環境，從當前目錄讀取
            self.config_path = Path.cwd() / config_path

        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加載配置檔案"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
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
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def reload(self):
        """重新加載配置檔案"""
        self.config = self._load_config()
