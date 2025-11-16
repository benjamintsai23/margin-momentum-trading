#!/bin/bash

# 融資融券動能交易系統 - 執行腳本
# 自動載入 .env 檔案並執行系統

# 載入 .env 檔案
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# 檢查是否提供了動作參數
if [ $# -eq 0 ]; then
    echo "使用方法: ./run.sh [analyze|test|backtest] [選項]"
    echo ""
    echo "動作："
    echo "  analyze                         分析今日融資融券訊號"
    echo "  analyze --date 2024-11-15       分析特定日期的訊號"
    echo "  test                            測試 Telegram 通知"
    echo "  backtest                        回測策略（預設從 2023-01-01）"
    echo "  backtest --start 2024-01-01     自訂回測開始日期"
    echo "  backtest --start 2024-01-01 --end 2024-11-15  自訂回測日期範圍"
    exit 1
fi

# 執行 Python 主程式，傳遞所有參數
python main.py "$@"
