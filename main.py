"""
融資融券動能交易系統 - 主程式
"""
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from src.config import Config
from src.utils.logger import Logger
from src.margin_momentum_analyzer import MarginMomentumAnalyzer
from src.telegram_notifier import TelegramNotifier
from src.backtest.backtest_engine import BacktestEngine

logger = Logger()


def main():
    """主程式入口"""

    # 驗證配置
    if not Config.validate():
        logger.error("配置檢查失敗，程式終止", "main")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='融資融券動能交易系統')
    parser.add_argument(
        'action',
        choices=['analyze', 'test', 'backtest'],
        help='執行動作: analyze=分析訊號, test=測試 Telegram, backtest=回測策略'
    )
    parser.add_argument(
        '--date',
        default=None,
        help='分析日期 (YYYY-MM-DD)，預設為昨日'
    )
    parser.add_argument(
        '--start',
        default='2023-01-01',
        help='回測開始日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        default=None,
        help='回測結束日期 (YYYY-MM-DD)，預設為昨日'
    )

    args = parser.parse_args()

    try:
        if args.action == 'analyze':
            analyze(args.date)
        elif args.action == 'test':
            test_telegram()
        elif args.action == 'backtest':
            backtest(args.start, args.end)

    except Exception as e:
        logger.critical(f"程式執行失敗: {e}", "main")
        sys.exit(1)


def analyze(analysis_date: str = None):
    """執行分析並發送通知"""

    logger.info("=" * 50, "main")
    logger.info("融資融券動能交易系統 - 開始分析", "main")
    logger.info("=" * 50, "main")

    try:
        # 初始化分析器和通知器
        analyzer = MarginMomentumAnalyzer()
        notifier = TelegramNotifier()

        # 執行分析
        signals = analyzer.analyze(analysis_date)

        # 過濾訊號
        if not signals.empty:
            signals = analyzer.filter_signals(signals)

        # 打印結果
        if not signals.empty:
            logger.info(f"發現 {len(signals)} 個訊號", "main")
            print("\n" + "=" * 80)
            print(signals.to_string())
            print("=" * 80)

            # 發送買訊通知
            buy_signals = signals[signals['訊號類型'] == 'BUY']
            if not buy_signals.empty:
                notifier.send_buy_signals(buy_signals)

            # 發送賣訊通知
            sell_signals = signals[signals['訊號類型'] == 'SELL']
            if not sell_signals.empty:
                notifier.send_sell_signals(sell_signals)

            # 發送每日摘要
            notifier.send_daily_summary(signals)

        else:
            logger.info("今日無異常訊號", "main")
            notifier.send_message("📊 融資融券動能分析完成\n\n✅ 今日無異常訊號", priority='normal')

        logger.info("分析完成！", "main")

    except Exception as e:
        logger.error(f"分析過程中發生錯誤: {e}", "main")
        raise


def backtest(start_date: str = '2023-01-01', end_date: str = None):
    """執行回測"""

    logger.info("=" * 50, "main")
    logger.info(f"開始回測: {start_date} ~ {end_date}", "main")
    logger.info("=" * 50, "main")

    try:
        # 確定結束日期
        if not end_date:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 初始化回測引擎
        engine = BacktestEngine(initial_capital=1000000)
        analyzer = MarginMomentumAnalyzer()

        # 定義策略函數
        def strategy(date_str):
            signals = analyzer.analyze(date_str)
            return signals if not signals.empty else None

        # 執行回測
        results = engine.run_backtest(start_date, end_date, strategy)

        # 打印結果摘要
        print("\n" + "=" * 80)
        print(f"回測結果摘要")
        print("=" * 80)
        print(f"初始資金: NT${results.initial_capital:,.0f}")
        print(f"最終資金: NT${results.final_capital:,.0f}")
        print(f"總報酬率: {results.total_return:.2%}")
        print(f"年化報酬率: {results.annual_return:.2%}")
        print(f"夏普比率: {results.sharpe_ratio:.2f}")
        print(f"最大回撤: {results.max_drawdown:.2%}")
        print(f"\n交易統計")
        print(f"總交易數: {results.total_trades}")
        print(f"獲利交易: {results.winning_trades}")
        print(f"虧損交易: {results.losing_trades}")
        print(f"勝率: {results.win_rate:.2%}")
        print("=" * 80 + "\n")

        logger.info("回測完成！", "main")

    except Exception as e:
        logger.error(f"回測過程中發生錯誤: {e}", "main")
        raise


def test_telegram():
    """測試 Telegram 通知功能"""

    logger.info("測試 Telegram 通知功能...", "main")
    notifier = TelegramNotifier()
    notifier.test_notification()


if __name__ == "__main__":
    main()
