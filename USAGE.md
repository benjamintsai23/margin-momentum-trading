# 使用說明

## 快速開始

### 配置環境變數

系統已經為你配置好 `.env` 檔案，包含：
- ✅ **FINLAB_TOKEN** - 已配置
- ✅ **TELEGRAM_BOT_TOKEN** - 已配置
- ✅ **TELEGRAM_CHAT_ID** - 已配置

## 執行系統

### macOS / Linux
\`\`\`bash
./run.sh test          # 測試 Telegram
./run.sh analyze       # 分析今日訊號
./run.sh backtest      # 回測策略
\`\`\`

### Windows (Command Prompt)
\`\`\`cmd
run.bat test           # 測試 Telegram
run.bat analyze        # 分析今日訊號
run.bat backtest       # 回測策略
\`\`\`

## 命令詳解

### 1. 測試 Telegram 通知
\`\`\`bash
./run.sh test
\`\`\`

### 2. 分析融資融券訊號
\`\`\`bash
./run.sh analyze
./run.sh analyze --date 2024-11-15
\`\`\`

### 3. 回測策略績效
\`\`\`bash
./run.sh backtest
./run.sh backtest --start 2024-01-01
./run.sh backtest --start 2024-01-01 --end 2024-11-15
\`\`\`

---

更多詳細資訊請查看 README.md

**最後更新**: 2024-11-16
