"""
日誌系統 - 統一管理所有日誌
"""
import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    """統一日誌管理器"""

    _loggers = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """取得或建立指定名稱的 logger"""
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 建立日誌目錄
        os.makedirs("logs", exist_ok=True)

        # 檔案處理器 - 輸出所有日誌到檔案
        log_file = f"logs/{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台處理器 - 輸出到終端
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 日誌格式
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # 避免重複添加處理器
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def info(cls, message: str, module: str = "main"):
        """記錄信息日誌"""
        logger = cls.get_logger(module)
        logger.info(f"ℹ️ {message}")

    @classmethod
    def debug(cls, message: str, module: str = "main"):
        """記錄調試日誌"""
        logger = cls.get_logger(module)
        logger.debug(f"🔍 {message}")

    @classmethod
    def warning(cls, message: str, module: str = "main"):
        """記錄警告日誌"""
        logger = cls.get_logger(module)
        logger.warning(f"⚠️ {message}")

    @classmethod
    def error(cls, message: str, module: str = "main"):
        """記錄錯誤日誌"""
        logger = cls.get_logger(module)
        logger.error(f"❌ {message}")

    @classmethod
    def critical(cls, message: str, module: str = "main"):
        """記錄嚴重錯誤"""
        logger = cls.get_logger(module)
        logger.critical(f"🚨 {message}")
