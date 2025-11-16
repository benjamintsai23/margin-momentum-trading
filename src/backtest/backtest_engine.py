"""
回測引擎 - 驗證融資融券動能策略的歷史績效
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.config import Config
from src.utils.logger import Logger
from src.utils.api_helper import FinLabAPIHelper

logger = Logger()


@dataclass
class Trade:
    """單一交易紀錄"""
    stock_id: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: int
    signal_type: str  # BUY or SELL
    signal_grade: str
    expected_return: float
    stop_loss: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # 'target', 'stop_loss', 'time', 'manual'
    holding_days: int


@dataclass
class BacktestResults:
    """回測結果"""
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    trades: List[Trade]
    equity_curve: pd.Series


class BacktestEngine:
    """回測引擎"""

    def __init__(self, initial_capital: float = 1000000):
        """
        初始化回測引擎

        Args:
            initial_capital: 初始資金
        """
        self.initial_capital = initial_capital
        self.api = FinLabAPIHelper()
        self.logger = logger

    def run_backtest(self,
                     start_date: str,
                     end_date: str,
                     strategy_func) -> BacktestResults:
        """
        執行回測

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            strategy_func: 策略函數，接收日期參數並返回該日期的訊號

        Returns:
            回測結果
        """
        try:
            self.logger.info(f"開始回測: {start_date} ~ {end_date}", "backtest")

            # 取得股價資料
            price_data = self.api.get_price_data()

            if price_data.empty:
                self.logger.error("無法取得股價資料", "backtest")
                raise ValueError("Stock price data not available")

            # 初始化回測變數
            trades = []
            equity_curve = {}
            current_capital = self.initial_capital
            holdings = {}  # {stock_id: {'shares': int, 'entry_price': float, 'entry_date': str}}

            # 日期範圍
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')

            # 迭代每個交易日
            for current_date in date_range:
                date_str = current_date.strftime('%Y-%m-%d')

                # 檢查股價資料中是否有該日期
                if date_str not in price_data.index:
                    continue

                # 取得當日訊號
                signals = strategy_func(date_str)

                if signals is None or signals.empty:
                    equity_curve[date_str] = current_capital
                    continue

                # 處理買訊
                buy_signals = signals[signals['訊號類型'] == 'BUY']
                for _, signal in buy_signals.iterrows():
                    stock_id = signal['股票代號']

                    if stock_id in holdings:
                        continue  # 已持有該股票

                    # 計算可投入資金
                    position_size = min(
                        self.initial_capital * Config.MAX_POSITION_SIZE,
                        current_capital * 0.1
                    )

                    # 計算股數
                    current_price = price_data.loc[date_str, stock_id] if stock_id in price_data.columns else np.nan

                    if pd.isna(current_price) or current_price == 0:
                        continue

                    shares = int(position_size / current_price)

                    if shares > 0:
                        # 進場
                        entry_cost = shares * current_price
                        current_capital -= entry_cost

                        holdings[stock_id] = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': date_str,
                            'signal_grade': signal['訊號等級'],
                            'expected_return': signal.get('預期報酬%', 10),
                            'stop_loss': signal.get('建議停損%', -8),
                            'holding_days': signal.get('建議持有天數', 5)
                        }

                        self.logger.debug(f"進場: {stock_id} @ {current_price}", "backtest")

                # 處理既有持倉
                stocks_to_remove = []
                for stock_id, holding in holdings.items():
                    if stock_id not in price_data.columns:
                        continue

                    current_price = price_data.loc[date_str, stock_id] if date_str in price_data.index else np.nan

                    if pd.isna(current_price) or current_price == 0:
                        continue

                    # 計算損益
                    entry_price = holding['entry_price']
                    entry_date = datetime.strptime(holding['entry_date'], '%Y-%m-%d')
                    holding_days = (current_date - entry_date).days

                    pnl = (current_price - entry_price) * holding['shares']
                    pnl_pct = (current_price - entry_price) / entry_price

                    # 檢查出場條件
                    exit_reason = None

                    # 1. 停利
                    if pnl_pct >= holding['expected_return'] / 100:
                        exit_reason = 'target'
                        exit_price = entry_price * (1 + holding['expected_return'] / 100)

                    # 2. 停損
                    elif pnl_pct <= holding['stop_loss'] / 100:
                        exit_reason = 'stop_loss'
                        exit_price = entry_price * (1 + holding['stop_loss'] / 100)

                    # 3. 持有天數到期
                    elif holding_days >= holding['holding_days']:
                        exit_reason = 'time'
                        exit_price = current_price

                    # 4. 有賣訊
                    elif not signals[signals['股票代號'] == stock_id].empty:
                        sell_signal = signals[signals['股票代號'] == stock_id]
                        if not sell_signal.empty and sell_signal.iloc[0]['訊號類型'] == 'SELL':
                            exit_reason = 'signal'
                            exit_price = current_price

                    # 如果有出場，執行出場
                    if exit_reason:
                        exit_proceeds = holding['shares'] * exit_price
                        current_capital += exit_proceeds

                        trade = Trade(
                            stock_id=stock_id,
                            entry_date=holding['entry_date'],
                            exit_date=date_str,
                            entry_price=entry_price,
                            exit_price=exit_price,
                            shares=holding['shares'],
                            signal_type='BUY',
                            signal_grade=holding['signal_grade'],
                            expected_return=holding['expected_return'],
                            stop_loss=holding['stop_loss'],
                            pnl=exit_proceeds - (entry_price * holding['shares']),
                            pnl_pct=(exit_price - entry_price) / entry_price,
                            exit_reason=exit_reason,
                            holding_days=holding_days
                        )

                        trades.append(trade)
                        stocks_to_remove.append(stock_id)

                        self.logger.debug(f"出場: {stock_id} @ {exit_price} ({exit_reason})", "backtest")

                # 移除已出場的持倉
                for stock_id in stocks_to_remove:
                    del holdings[stock_id]

                # 記錄資金曲線
                holding_value = sum(
                    price_data.loc[date_str, stock_id] * holding['shares']
                    for stock_id, holding in holdings.items()
                    if stock_id in price_data.columns and date_str in price_data.index
                )
                equity_curve[date_str] = current_capital + holding_value

            # 計算績效指標
            results = self._calculate_metrics(
                trades,
                pd.Series(equity_curve),
                start_date,
                end_date
            )

            self.logger.info(f"回測完成: 總報酬 {results.total_return:.2%}, 年化 {results.annual_return:.2%}", "backtest")

            return results

        except Exception as e:
            self.logger.error(f"回測失敗: {e}", "backtest")
            raise

    def _calculate_metrics(self,
                          trades: List[Trade],
                          equity_curve: pd.Series,
                          start_date: str,
                          end_date: str) -> BacktestResults:
        """計算績效指標"""

        if len(trades) == 0:
            return BacktestResults(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=equity_curve.iloc[-1] if len(equity_curve) > 0 else self.initial_capital,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_return=0,
                annual_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                trades=trades,
                equity_curve=equity_curve
            )

        # 計算基本指標
        final_capital = equity_curve.iloc[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # 年化報酬率
        days = (datetime.strptime(end_date, '%Y-%m-%d') -
                datetime.strptime(start_date, '%Y-%m-%d')).days
        years = days / 365
        annual_return = (final_capital / self.initial_capital) ** (1 / years) - 1 if years > 0 else 0

        # 交易統計
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl <= 0])
        win_rate = winning_trades / len(trades) if len(trades) > 0 else 0

        # 夏普比率
        daily_returns = equity_curve.pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

        # 最大回撤
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_drawdown = drawdown.min()

        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            trades=trades,
            equity_curve=equity_curve
        )
