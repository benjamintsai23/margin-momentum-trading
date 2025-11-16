"""
FinLab API 輔助工具 - 帶重試機制和錯誤處理
"""
import time
from typing import Any, Dict, List, Optional
import pandas as pd
from src.config import Config
from src.utils.logger import Logger

logger_instance = Logger()

def retry_on_failure(max_attempts: int = 3, delay: float = 5.0, backoff: float = 2.0):
    """重試裝飾器 - 自動重試失敗的 API 呼叫"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts:
                        logger_instance.warning(
                            f"API 呼叫失敗 (嘗試 {attempt}/{max_attempts}): {str(e)}",
                            "api_helper"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                        attempt += 1
                    else:
                        logger_instance.error(
                            f"API 呼叫在 {max_attempts} 次嘗試後仍失敗: {str(e)}",
                            "api_helper"
                        )
                        raise

        return wrapper
    return decorator


class FinLabAPIHelper:
    """FinLab API 輔助類"""

    def __init__(self, token: Optional[str] = None):
        """初始化 FinLab 連接"""
        self.token = token or Config.FINLAB_TOKEN
        self._init_finlab()

    def _init_finlab(self):
        """初始化 FinLab 連接"""
        try:
            import finlab
            finlab.login(self.token)
            logger_instance.info("✅ FinLab 連接成功", "api_helper")
        except Exception as e:
            logger_instance.error(f"FinLab 連接失敗: {e}", "api_helper")
            raise

    @retry_on_failure(max_attempts=3, delay=5.0)
    def get_data(self, key: str, **kwargs) -> pd.DataFrame:
        """
        取得單一資料集

        Args:
            key: 資料鍵名稱 (例: 'price:收盤價', 'margin_transactions:融資今日餘額')
            **kwargs: 傳遞給 finlab.data.get() 的其他參數

        Returns:
            pandas DataFrame
        """
        try:
            from finlab import data
            result = data.get(key, **kwargs)
            logger_instance.debug(f"成功取得資料: {key}", "api_helper")
            return result
        except Exception as e:
            logger_instance.error(f"無法取得資料 {key}: {e}", "api_helper")
            raise

    @retry_on_failure(max_attempts=3, delay=5.0)
    def get_multiple_data(self, keys: List[str]) -> Dict[str, pd.DataFrame]:
        """
        批量取得多個資料集（並行取得，更高效）

        Args:
            keys: 資料鍵列表

        Returns:
            字典，鍵為資料鍵名稱，值為 DataFrame
        """
        try:
            import finlab
            data = {}
            logger_instance.info(f"開始批量取得 {len(keys)} 個資料集", "api_helper")

            for key in keys:
                try:
                    data[key] = self.get_data(key)
                except Exception as e:
                    logger_instance.warning(f"無法取得 {key}，跳過: {e}", "api_helper")
                    continue

            logger_instance.info(f"成功取得 {len(data)}/{len(keys)} 個資料集", "api_helper")
            return data

        except Exception as e:
            logger_instance.error(f"批量取得資料失敗: {e}", "api_helper")
            raise

    def get_margin_data(self) -> Dict[str, pd.DataFrame]:
        """
        取得融資融券相關資料

        Returns:
            包含融資融券數據的字典
        """
        keys = [
            'margin_transactions:融資買進',
            'margin_transactions:融資賣出',
            'margin_transactions:融資前日餘額',
            'margin_transactions:融資今日餘額',
            'margin_transactions:融資使用率',
            'margin_transactions:融券買進',
            'margin_transactions:融券賣出',
            'margin_transactions:融券前日餘額',
            'margin_transactions:融券今日餘額',
            'margin_transactions:融券使用率',
            'margin_transactions:資券互抵',
        ]

        return self.get_multiple_data(keys)

    def get_price_data(self) -> pd.DataFrame:
        """取得股票收盤價"""
        return self.get_data('price:收盤價')

    def get_volume_data(self) -> pd.DataFrame:
        """取得股票成交股數"""
        return self.get_data('price:成交股數')

    def get_open_price(self) -> pd.DataFrame:
        """取得股票開盤價"""
        return self.get_data('price:開盤價')

    def get_high_price(self) -> pd.DataFrame:
        """取得股票最高價"""
        return self.get_data('price:最高價')

    def get_low_price(self) -> pd.DataFrame:
        """取得股票最低價"""
        return self.get_data('price:最低價')
