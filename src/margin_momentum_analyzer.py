"""
融資融券 + 動能分析器
核心策略模組 - 偵測異常訊號並生成買賣建議
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from src.config import Config
from src.utils.logger import Logger
from src.utils.api_helper import FinLabAPIHelper

logger = Logger()


class TechnicalIndicators:
    """技術面指標計算"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        計算 RSI (相對強度指數)
        RSI = 100 - (100 / (1 + RS))
        where RS = 平均漲幅 / 平均跌幅
        """
        if len(prices) < period + 1:
            return pd.Series(np.nan, index=prices.index)
            
        deltas = prices.diff()
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices, dtype=float)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas.iloc[i]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period

            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return pd.Series(rsi, index=prices.index)

    @staticmethod
    def calculate_ma(prices: pd.Series, period: int) -> pd.Series:
        """計算簡單移動平均線 (SMA)"""
        return prices.rolling(window=period).mean()


class MarginMomentumAnalyzer:
    """融資融券 + 動能分析器"""

    def __init__(self):
        """初始化分析器"""
        self.api = FinLabAPIHelper()
        self.logger = logger
        self.config = Config

    def analyze(self, analysis_date: Optional[str] = None) -> pd.DataFrame:
        """
        執行完整分析

        Args:
            analysis_date: 分析日期 (格式: YYYY-MM-DD)，預設為昨日

        Returns:
            包含買賣訊號的 DataFrame
        """
        try:
            # 確定分析日期
            if not analysis_date:
                analysis_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

            self.logger.info(f"開始分析融資融券 + 動能訊號: {analysis_date}", "analyzer")

            # 取得資料
            self.logger.info("正在取得 FinLab 資料...", "analyzer")
            margin_data = self.api.get_margin_data()
            price_data = self.api.get_price_data()

            # 檢查資料是否為空
            if not margin_data or isinstance(margin_data, dict) and all(
                isinstance(v, pd.DataFrame) and v.empty for v in margin_data.values()
            ):
                self.logger.warning("融資融券資料為空", "analyzer")
                return pd.DataFrame()

            if isinstance(price_data, pd.DataFrame) and price_data.empty:
                self.logger.warning("股價資料為空", "analyzer")
                return pd.DataFrame()

            # 計算技術指標
            self.logger.info("計算技術指標 (RSI、MA)...", "analyzer")
            if isinstance(price_data, pd.DataFrame) and len(price_data) > 0:
                first_col = price_data.iloc[:, 0]
                rsi = TechnicalIndicators.calculate_rsi(first_col, Config.RSI_PERIOD)
                ma5 = TechnicalIndicators.calculate_ma(first_col, Config.MA_SHORT)
                ma20 = TechnicalIndicators.calculate_ma(first_col, Config.MA_MEDIUM)
            else:
                self.logger.warning("無足夠的股價資料計算技術指標", "analyzer")
                return pd.DataFrame()

            # 偵測融資融券異常
            self.logger.info("偵測融資融券異常訊號...", "analyzer")
            signals = self._detect_margin_anomalies(
                margin_data,
                price_data,
                rsi, ma5, ma20,
                analysis_date
            )

            self.logger.info(f"分析完成，發現 {len(signals)} 個訊號", "analyzer")
            return signals

        except Exception as e:
            self.logger.error(f"分析過程中發生錯誤: {e}", "analyzer")
            raise

    def _detect_margin_anomalies(self,
                                  margin_data: Dict,
                                  price_data: pd.DataFrame,
                                  rsi: pd.Series,
                                  ma5: pd.Series,
                                  ma20: pd.Series,
                                  analysis_date: str) -> pd.DataFrame:
        """
        偵測融資融券異常並結合技術面指標

        Returns:
            包含買賣訊號的 DataFrame
        """
        signals = []

        # 取得融資融券資料
        if not margin_data or not isinstance(margin_data, dict):
            return pd.DataFrame()

        margin_balance_df = margin_data.get('融資今日餘額')
        if margin_balance_df is None or margin_balance_df.empty:
            self.logger.warning("無融資餘額資料", "analyzer")
            return pd.DataFrame()

        # 遍歷每支股票
        for stock_id in price_data.columns[:20]:  # 限制前 20 支股票以提高效能
            try:
                # 獲取股價
                if stock_id not in price_data.columns:
                    continue

                current_price = price_data[stock_id].iloc[-1] if len(price_data) > 0 else np.nan

                if pd.isna(current_price) or current_price <= 0:
                    continue

                # 獲取融資融券資料
                if stock_id not in margin_balance_df.columns:
                    continue

                margin_balance = margin_balance_df[stock_id].iloc[-1] if len(margin_balance_df) > 0 else 0

                # 獲取技術指標
                rsi_value = rsi[stock_id].iloc[-1] if stock_id in rsi.index else np.nan
                ma20_value = ma20[stock_id].iloc[-1] if stock_id in ma20.columns else np.nan

                if pd.isna(rsi_value) or pd.isna(ma20_value):
                    continue

                price_vs_ma20 = (current_price - ma20_value) / ma20_value if ma20_value > 0 else 0

                # 買訊檢測：融資異常 + RSI 超賣 + 股價在 MA20 下方
                if (margin_balance > 0 and 
                    rsi_value < self.config.RSI_OVERSOLD and 
                    price_vs_ma20 < 0):

                    signal_grade = 'S級' if rsi_value < 25 else 'A級'

                    signals.append({
                        '股票代號': stock_id,
                        '分析日期': analysis_date,
                        '訊號類型': 'BUY',
                        '訊號等級': signal_grade,
                        '現股價': round(current_price, 2),
                        'RSI': round(rsi_value, 2),
                        'MA20': round(ma20_value, 2),
                        '融資餘額': int(margin_balance),
                        '異常訊號': f"RSI超賣({rsi_value:.1f})",
                        '預期報酬%': 15 if signal_grade == 'S級' else 10,
                        '建議停損%': -8,
                        '建議持有天數': 5
                    })

            except Exception as e:
                self.logger.debug(f"處理股票 {stock_id} 時出錯: {e}", "analyzer")
                continue

        return pd.DataFrame(signals) if signals else pd.DataFrame()

    def filter_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        過濾訊號 - 移除低質量訊號

        Returns:
            過濾後的訊號 DataFrame
        """
        if signals.empty:
            return signals

        # 移除股價過低或過高的訊號
        signals = signals[
            (signals['現股價'] >= self.config.MIN_STOCK_PRICE) &
            (signals['現股價'] <= self.config.MAX_STOCK_PRICE)
        ]

        # 排序：優先顯示高等級訊號
        signal_order = {'S級': 0, 'A級': 1, 'B級': 2, 'URGENT': 3, 'HIGH': 4}
        signals['grade_order'] = signals['訊號等級'].map(signal_order)
        signals = signals.sort_values('grade_order').drop('grade_order', axis=1)

        return signals
