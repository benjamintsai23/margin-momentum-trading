"""
配置管理模組 - 融資融券動能交易系統
"""
import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

class Config:
    """系統配置"""

    # API Keys - 從環境變數讀取
    FINLAB_TOKEN = os.getenv("FINLAB_TOKEN")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # FinLab 設定
    FINLAB_API_URL = "https://api.finlab.tw"

    # Telegram 設定
    TELEGRAM_API_URL = "https://api.telegram.org"

    # 系統設定
    TIMEZONE = "Asia/Taipei"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # ===== 融資融券策略參數 =====

    # 融資異常檢測
    MARGIN_INCREASE_THRESHOLD = 0.10  # 融資餘額增加 10% 視為異常
    MARGIN_USAGE_THRESHOLD = 0.80     # 融資使用率 > 80% 高風險
    MARGIN_BUY_MA_PERIOD = 3          # 融資買進 3 日均線

    # 融券異常檢測
    SHORT_INCREASE_THRESHOLD = 0.10   # 融券餘額增加 10% 視為異常
    SHORT_TO_MARGIN_RATIO = 0.5       # 融券/融資比例 > 0.5 異常訊號
    SHORT_SELL_MA_PERIOD = 3          # 融券賣出 3 日均線

    # 資券互抵異常
    OFFSET_THRESHOLD = 100000         # 資券互抵 > 100,000 視為異常

    # 技術面動能參數
    RSI_PERIOD = 14                   # RSI 週期
    RSI_OVERSOLD = 30                 # RSI 超賣線
    RSI_OVERBOUGHT = 70               # RSI 超買線

    MA_SHORT = 5                      # 短期均線 (5日)
    MA_MEDIUM = 20                    # 中期均線 (20日)
    MA_LONG = 60                      # 長期均線 (60日)

    # 訊號評級規則
    BUY_SIGNAL_GRADE = {
        'S級': {
            'margin_abnormal': True,      # 融資異常
            'rsi_oversold': True,         # RSI 超賣
            'price_below_ma20': True,     # 股價在 MA20 下方
            'expected_return': (0.10, 0.30)  # 預期報酬 10-30%
        },
        'A級': {
            'margin_abnormal': True,
            'rsi_oversold': False,        # RSI 不超賣但仍低
            'price_below_ma20': True,
            'expected_return': (0.08, 0.20)  # 預期報酬 8-20%
        },
        'B級': {
            'margin_abnormal': False,
            'rsi_oversold': True,
            'price_below_ma20': True,
            'expected_return': (0.05, 0.15)  # 預期報酬 5-15%
        }
    }

    SELL_SIGNAL_GRADE = {
        'URGENT': {
            'short_abnormal': True,       # 融券異常
            'rsi_overbought': True,       # RSI 超買
            'price_above_ma20': True,     # 股價在 MA20 上方
        },
        'HIGH': {
            'short_abnormal': True,
            'rsi_overbought': False,
            'price_above_ma20': True,
        }
    }

    # 交易參數
    HOLDING_DAYS = 5                 # 預期持有天數
    STOP_LOSS_PCT = -0.08            # 停損 -8%
    TAKE_PROFIT_PCT = 0.15           # 停利 +15%

    # 倉位管理
    MAX_HOLDINGS = 10                # 最多同時持有 10 檔股票
    MAX_POSITION_SIZE = 0.10         # 單檔最大倉位 10%
    TOTAL_POSITION_LIMIT = 0.80      # 總倉位限制 80%

    # 過濾條件
    MIN_STOCK_PRICE = 10             # 最低股價 NT$10
    MAX_STOCK_PRICE = 500            # 最高股價 NT$500
    MIN_DAILY_VOLUME = 1000000       # 最少日成交額 100 萬

    @classmethod
    def validate(cls):
        """驗證必要的設定是否存在"""
        errors = []

        # 檢查必要的 API Keys
        if not cls.FINLAB_TOKEN:
            errors.append("❌ FINLAB_TOKEN 未設定")

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("⚠️ TELEGRAM_BOT_TOKEN 未設定（Telegram 通知將無法使用）")

        if not cls.TELEGRAM_CHAT_ID:
            errors.append("⚠️ TELEGRAM_CHAT_ID 未設定（Telegram 通知將無法使用）")

        # 顯示錯誤訊息
        if errors:
            print("\n⚠️ 設定檢查：")
            for error in errors:
                print(f"   {error}")

            # 如果有必要的設定缺失，回傳 False
            critical_errors = [e for e in errors if e.startswith("❌")]
            if critical_errors:
                return False

        return True
