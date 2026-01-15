"""
工具函數模組
"""
import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """
    獲取資源文件路徑（支持 PyInstaller 打包）
    
    Args:
        relative_path: 相對路徑
    
    Returns:
        實際資源路徑
    """
    if getattr(sys, 'frozen', False):
        # 打包後，優先使用外部資源
        external_path = Path(sys.executable).parent / relative_path
        if external_path.exists():
            return str(external_path)
        # 使用打包內的資源
        base_path = Path(getattr(sys, '_MEIPASS', ''))
    else:
        # 開發環境
        base_path = Path.cwd()
    
    return str(base_path / relative_path)
