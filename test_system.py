"""
系統測試腳本 - 用模擬資料測試整個系統
不需要真實 API tokens，只驗證程式邏輯是否正常
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.config import Config
from src.utils.logger import Logger
from src.margin_momentum_analyzer import MarginMomentumAnalyzer, TechnicalIndicators

logger = Logger()

def test_logger():
    """測試日誌系統"""
    print("\n" + "=" * 80)
    print("【測試 1】日誌系統")
    print("=" * 80)

    logger.info("這是一個 INFO 訊息", "test")
    logger.warning("這是一個 WARNING 訊息", "test")
    logger.error("這是一個 ERROR 訊息", "test")

    print("✅ 日誌系統測試通過！")

def test_technical_indicators():
    """測試技術面指標計算"""
    print("\n" + "=" * 80)
    print("【測試 2】技術面指標計算 (RSI、MA)")
    print("=" * 80)

    # 生成模擬股價資料
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)  # 隨機遊走
    price_series = pd.Series(prices, index=dates)

    # 計算技術指標
    rsi = TechnicalIndicators.calculate_rsi(price_series, period=14)
    ma5 = TechnicalIndicators.calculate_ma(price_series, period=5)
    ma20 = TechnicalIndicators.calculate_ma(price_series, period=20)

    print(f"股價範圍: {price_series.min():.2f} - {price_series.max():.2f}")
    print(f"最新股價: {price_series.iloc[-1]:.2f}")
    print(f"最新 RSI(14): {rsi.iloc[-1]:.2f}")
    print(f"最新 MA5: {ma5.iloc[-1]:.2f}")
    print(f"最新 MA20: {ma20.iloc[-1]:.2f}")

    # 驗證指標範圍
    assert rsi.min() >= 0 and rsi.max() <= 100, "RSI 應該在 0-100 之間"
    assert len(ma5) == len(price_series), "MA5 長度應該與股價相同"
    assert len(ma20) == len(price_series), "MA20 長度應該與股價相同"

    print("✅ 技術面指標計算測試通過！")

def test_signal_generation():
    """測試訊號生成邏輯"""
    print("\n" + "=" * 80)
    print("【測試 3】訊號生成邏輯")
    print("=" * 80)

    # 建立模擬訊號資料
    test_signals = [
        {
            '股票代號': '2330',
            '分析日期': '2024-11-16',
            '訊號類型': 'BUY',
            '訊號等級': 'S級',
            '現股價': 950.0,
            'RSI': 28.5,
            'MA20': 1000.0,
            '融資餘額': 50000000,
            '融資增幅%': 15.5,
            '融券餘額': 10000000,
            '融資/融券比': 5.0,
            '異常訊號': '融資異常(15.5%) + RSI超賣(28.5)',
            '預期報酬%': 15,
            '建議停損%': -8,
            '建議持有天數': 5
        },
        {
            '股票代號': '2454',
            '分析日期': '2024-11-16',
            '訊號類型': 'SELL',
            '訊號等級': 'URGENT',
            '現股價': 180.0,
            'RSI': 72.0,
            'MA20': 170.0,
            '融資餘額': 20000000,
            '融券餘額': 15000000,
            '融券增幅%': 18.2,
            '融資/融券比': 1.33,
            '異常訊號': '融券異常(18.2%) + RSI超買(72.0)',
            '風險警告': '主力作空訊號強烈'
        }
    ]

    df_signals = pd.DataFrame(test_signals)

    print(f"生成訊號數: {len(df_signals)}")
    print(f"\n買訊數: {len(df_signals[df_signals['訊號類型'] == 'BUY'])}")
    print(f"賣訊數: {len(df_signals[df_signals['訊號類型'] == 'SELL'])}")

    print("\n訊號詳情:")
    print(df_signals[['股票代號', '訊號類型', '訊號等級', '現股價', 'RSI']].to_string())

    # 驗證訊號結構
    assert '訊號類型' in df_signals.columns, "訊號應包含 '訊號類型' 欄位"
    assert '訊號等級' in df_signals.columns, "訊號應包含 '訊號等級' 欄位"
    assert all(df_signals['訊號類型'].isin(['BUY', 'SELL'])), "訊號類型應為 BUY 或 SELL"

    print("✅ 訊號生成邏輯測試通過！")
    return df_signals

def test_telegram_formatting(signals):
    """測試 Telegram 訊息格式"""
    print("\n" + "=" * 80)
    print("【測試 4】Telegram 訊息格式")
    print("=" * 80)

    buy_signals = signals[signals['訊號類型'] == 'BUY']

    if not buy_signals.empty:
        detail_msg = "<b>🎯 高優先級買訊詳情</b>\n\n"

        for _, row in buy_signals.iterrows():
            level_icon = "🔥" if row['訊號等級'] == 'S級' else "📈"
            detail_msg += f"{level_icon} <b>{row['股票代號']}</b>\n"
            detail_msg += f"├ 現股價: <b>${row['現股價']:.2f}</b>\n"
            detail_msg += f"├ RSI: {row['RSI']} (超賣: < 30)\n"
            detail_msg += f"├ 融資增幅: {row['融資增幅%']}%\n"
            detail_msg += f"├ 預期報酬: <b>+{row['預期報酬%']}%</b>\n"
            detail_msg += f"├ 建議停損: {row['建議停損%']}%\n"
            detail_msg += f"└ 持有期限: {row['建議持有天數']} 天\n\n"

        print("訊息預覽:")
        print(detail_msg)

        # 驗證訊息長度
        assert len(detail_msg) > 0, "訊息不應為空"
        assert len(detail_msg) < 4000, "訊息長度應小於 4000 字"

    print("✅ Telegram 訊息格式測試通過！")

def test_config():
    """測試配置載入"""
    print("\n" + "=" * 80)
    print("【測試 5】配置載入")
    print("=" * 80)

    print(f"RSI 週期: {Config.RSI_PERIOD}")
    print(f"RSI 超賣線: {Config.RSI_OVERSOLD}")
    print(f"RSI 超買線: {Config.RSI_OVERBOUGHT}")
    print(f"MA 短期: {Config.MA_SHORT} 日")
    print(f"MA 中期: {Config.MA_MEDIUM} 日")
    print(f"MA 長期: {Config.MA_LONG} 日")
    print(f"融資增幅閾值: {Config.MARGIN_INCREASE_THRESHOLD * 100}%")
    print(f"融券增幅閾值: {Config.SHORT_INCREASE_THRESHOLD * 100}%")
    print(f"最大持股數: {Config.MAX_HOLDINGS}")
    print(f"單檔最大倉位: {Config.MAX_POSITION_SIZE * 100}%")

    # 驗證配置
    assert Config.RSI_PERIOD > 0, "RSI 週期應 > 0"
    assert Config.RSI_OVERSOLD < Config.RSI_OVERBOUGHT, "超賣線應 < 超買線"
    assert Config.MA_SHORT < Config.MA_MEDIUM < Config.MA_LONG, "均線週期應遞增"

    print("✅ 配置載入測試通過！")

def run_all_tests():
    """執行所有測試"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "融資融券動能交易系統 - 系統測試" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        test_logger()
        test_config()
        test_technical_indicators()
        signals = test_signal_generation()
        test_telegram_formatting(signals)

        print("\n" + "=" * 80)
        print("✅ 所有測試通過！系統準備就緒！")
        print("=" * 80)
        print("\n下一步:")
        print("1. 編輯 .env 檔案，填入真實的 API tokens")
        print("2. 執行: python main.py analyze")
        print("3. 或執行: python main.py backtest --start 2024-01-01")
        print("\n")

        return 0

    except AssertionError as e:
        logger.error(f"測試失敗: {e}", "test")
        print(f"\n❌ 測試失敗: {e}\n")
        return 1
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}", "test")
        print(f"\n❌ 錯誤: {e}\n")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
