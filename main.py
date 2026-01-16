#!/usr/bin/env python

"""
釣魚自動化主程式
"""
import time
import sys
from pathlib import Path
from src.fishing_bot import FishingBot
from src.config_manager import ConfigManager
from src.logger import setup_logger


def get_version() -> str:
    """取得版本號，優先讀取 VERSION 檔，找不到時回退到套件版本。"""
    version_file = Path(__file__).parent / "VERSION"

    try:
        return version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        pass

    try:
        from src import __version__

        return __version__
    except Exception:
        return "unknown"


def main():
    """主函數"""
    config = ConfigManager('config.yaml')

    logger = setup_logger(
        config.get('logging.level', 'INFO'),
        config.get('logging.file', 'fishing_bot.log')
    )

    version = get_version()

    logger.info("=" * 50)
    logger.info(f"釣魚機器人 {version}")
    logger.info("Python version: " + sys.version)
    logger.info("=" * 50)
    logger.info("釣魚機器人啟動")
    logger.info("=" * 50)

    try:
        # 創建釣魚機器人實例
        bot = FishingBot(config)

        # 檢查遊戲視窗
        if not bot.find_game_window():
            logger.error("未找到遊戲視窗，請檢查設定檔中的視窗標題")
            return

        logger.info("找到遊戲視窗，準備開始釣魚...")

        time.sleep(2)

        # 開始釣魚循環
        bot.start()

    except KeyboardInterrupt:
        logger.info("\n用戶中斷程式")
    except Exception as e:
        logger.error(f"程式異常: {e}", exc_info=True)
    finally:
        logger.info("程式結束")
        #停止以便查看日誌
        input("按下 Enter 鍵以退出...")

if __name__ == "__main__":
    main()
