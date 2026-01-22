"""
日誌模組
"""

import logging
import sys
from pathlib import Path


def setup_logger(
    level: str = "INFO", log_file: str | None = None
) -> logging.Logger:
    """
    設置日誌紀錄器

    Args:
        level: 日誌級別
        log_file: 日誌檔案路徑

    Returns:
        配置好的日誌紀錄器
    """
    # 創建日誌紀錄器
    logger = logging.getLogger("FishingBot")
    logger.setLevel(getattr(logging, level.upper()))

    # 清除已有的處理器
    logger.handlers.clear()

    # 創建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 檔案處理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
