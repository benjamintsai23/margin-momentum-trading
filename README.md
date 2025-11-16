# 融資融券動能交易系統

一個基於融資融券異常 + 技術面動能的台股自動交易訊號系統。

## 🎯 策略邏輯

### 核心理念
結合 **融資融券市場訊號** 和 **技術面動能指標** 來識別高概率交易機會。

### 買訊規則
```
✅ 買訊 = 融資異常（散戶追高）+ RSI 超賣（技術超賣）+ 股價在 MA20 下方

等級分類：
  🔥 S級：融資增幅 > 15% + RSI < 25 + 股價跌超 5%
         → 預期報酬：10-30%

  📈 A級：融資增幅 > 10% + RSI < 30 + 股價下跌
         → 預期報酬：8-20%

  ⚡ B級：融資異常 + RSI < 30
         → 預期報酬：5-15%
```

### 賣訊規則
```
⚠️ 賣訊 = 融券異常（主力作空）+ RSI 超買（技術超買）+ 股價在 MA20 上方

等級分類：
  🔴 URGENT：融券增幅 > 15% + RSI > 75 + 股價上漲
            → 立即行動

  🟠 HIGH：融券異常 + RSI > 70
           → 準備出場
```

## 📊 技術指標

| 指標 | 週期 | 用途 |
|------|------|------|
| RSI | 14 日 | 判斷超買/超賣 |
| MA 5 | 5 日 | 短期趨勢 |
| MA 20 | 20 日 | 中期趨勢 |
| MA 60 | 60 日 | 長期趨勢 |
| MACD | 12/26/9 | 動能確認（預留） |

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 配置環境變數
```bash
# 複製 .env.example 為 .env
cp .env.example .env

# 編輯 .env 並填入你的 API Keys：
FINLAB_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
GOOGLE_SHEETS_ID=your_sheets_id
```

### 3. 執行分析
```bash
# 分析今日訊號
python main.py analyze

# 分析特定日期
python main.py analyze --date 2024-11-15

# 測試 Telegram 通知
python main.py test
```

## 📁 專案結構
```
margin-momentum-trading/
├── src/
│   ├── config.py                    # 配置管理
│   ├── margin_momentum_analyzer.py   # 核心分析器
│   ├── telegram_notifier.py         # Telegram 通知
│   ├── utils/
│   │   ├── logger.py                # 日誌系統
│   │   └── api_helper.py            # API 輔助
│   └── __init__.py
├── main.py                          # 主程式入口
├── requirements.txt                 # 依賴清單
├── .env.example                     # 環境變數範例
├── README.md                        # 本檔案
├── data/                            # 資料儲存
├── logs/                            # 日誌檔案
└── reports/                         # 報告輸出
```

## 🔧 配置詳解

編輯 `src/config.py` 中的策略參數：

### 融資融券閾值
```python
MARGIN_INCREASE_THRESHOLD = 0.10      # 融資增加 10% 視為異常
MARGIN_USAGE_THRESHOLD = 0.80         # 融資使用率 > 80% 高風險
SHORT_INCREASE_THRESHOLD = 0.10       # 融券增加 10% 視為異常
SHORT_TO_MARGIN_RATIO = 0.5          # 融券/融資比 > 0.5 異常
```

### 技術指標參數
```python
RSI_PERIOD = 14                       # RSI 週期
RSI_OVERSOLD = 30                     # RSI 超賣線
RSI_OVERBOUGHT = 70                   # RSI 超買線
MA_SHORT = 5                          # 短期均線
MA_MEDIUM = 20                        # 中期均線
MA_LONG = 60                          # 長期均線
```

### 交易管理
```python
HOLDING_DAYS = 5                      # 預期持有 5 天
STOP_LOSS_PCT = -0.08                # 停損 -8%
TAKE_PROFIT_PCT = 0.15               # 停利 +15%
MAX_HOLDINGS = 10                     # 最多持有 10 檔
MAX_POSITION_SIZE = 0.10             # 單檔最大 10% 倉位
```

## 📱 Telegram 通知

系統會自動發送三種類型通知：

1. **摘要通知**（靜音）
   - 發現訊號數量統計
   - 按等級分類統計

2. **詳細通知**（有聲）
   - S級 和 A級 訊號的詳細資訊
   - 包含現價、預期報酬、停損位

3. **日報通知**（靜音）
   - 每日交易總結
   - TOP 3 機會

## 🔐 資料安全

- ✅ API Keys 存放在 `.env` 中（不上傳到 Git）
- ✅ `credentials.json` 本地保存（不上傳）
- ✅ 敏感訊息通過 Telegram 加密傳輸
- ✅ 所有日誌存放在 `logs/` 目錄

## ⚠️ 風險免責

本系統僅供教育和研究之用。使用本系統進行交易時，請：

1. 充分理解市場風險
2. 不投入超過自己承受能力的資金
3. 嚴格遵守停損規則
4. 定期檢視策略績效

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📝 許可證

MIT License

---

**最後更新**：2024-11-16
**版本**：1.0.0
