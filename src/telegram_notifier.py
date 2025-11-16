"""
Telegram 通知模組 - 融資融券動能交易系統
"""
import requests
import time
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from src.config import Config
from src.utils.logger import Logger

logger = Logger()


class TelegramNotifier:
    """Telegram 推播通知器"""

    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message: str, priority: str = 'normal', disable_notification: Optional[bool] = None):
        """
        發送訊息到 Telegram

        Args:
            message: 要發送的訊息
            priority: 優先級 ('urgent', 'high', 'normal', 'low')
            disable_notification: 是否靜音通知
        """
        try:
            url = f"{self.base_url}/sendMessage"

            # 如果訊息太長，截斷它
            if len(message) > 4000:
                message = message[:3950] + "\n\n... 訊息過長，請查看 Google Sheets"

            # 根據優先級加入特殊標記
            if priority == 'urgent':
                message = "🚨 " + message
            elif priority == 'high':
                message = "🔔 " + message

            # 決定是否靜音
            if disable_notification is None:
                disable_notification = priority in ['normal', 'low']

            response = requests.post(url, data={
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_notification': disable_notification
            })

            result = response.json()
            if result['ok']:
                logger.info(f"Telegram 訊息已發送 (優先級: {priority})", "telegram")
                return True
            else:
                logger.error(f"Telegram API 錯誤: {result}", "telegram")
                return False

        except Exception as e:
            logger.error(f"Telegram 發送失敗: {e}", "telegram")
            return False

    def send_buy_signals(self, signals: pd.DataFrame):
        """發送買訊警報"""
        if signals.empty:
            return

        buy_signals = signals[signals['訊號類型'] == 'BUY']
        if buy_signals.empty:
            return

        # 摘要訊息
        summary_msg = "<b>🚀 融資融券動能買訊分析</b>\n"
        summary_msg += f"📅 {buy_signals.iloc[0]['分析日期']}\n"
        summary_msg += f"📊 發現買訊: {len(buy_signals)} 個\n\n"

        # 統計等級數量
        s_count = len(buy_signals[buy_signals['訊號等級'] == 'S級'])
        a_count = len(buy_signals[buy_signals['訊號等級'] == 'A級'])

        summary_msg += f"🔥 S級訊號: {s_count} 個\n"
        summary_msg += f"📈 A級訊號: {a_count} 個\n\n"

        # 發送摘要
        self.send_message(summary_msg, priority='normal')

        # 發送詳細訊號（S級和A級）
        high_priority = buy_signals[buy_signals['訊號等級'].isin(['S級', 'A級'])]

        if not high_priority.empty:
            time.sleep(1)

            detail_msg = "<b>🎯 高優先級買訊詳情</b>\n\n"

            for _, row in high_priority.iterrows():
                level_icon = "🔥" if row['訊號等級'] == 'S級' else "📈"

                detail_msg += f"{level_icon} <b>{row['股票代號']}</b>\n"
                detail_msg += f"├ 現股價: <b>${row['現股價']:.2f}</b>\n"
                detail_msg += f"├ RSI: {row['RSI']} (超賣: < 30)\n"
                detail_msg += f"├ 融資增幅: {row['融資增幅%']}%\n"
                detail_msg += f"├ 預期報酬: <b>+{row['預期報酬%']}%</b>\n"
                detail_msg += f"├ 建議停損: {row['建議停損%']}%\n"
                detail_msg += f"└ 持有期限: {row['建議持有天數']} 天\n\n"

            # 限制訊息長度
            if len(detail_msg) > 3500:
                detail_msg = detail_msg[:3450] + "\n\n... 更多訊號請查看 Google Sheets"

            self.send_message(detail_msg, priority='high')

    def send_sell_signals(self, signals: pd.DataFrame):
        """發送賣訊警報"""
        if signals.empty:
            return

        sell_signals = signals[signals['訊號類型'] == 'SELL']
        if sell_signals.empty:
            return

        urgent_signals = sell_signals[sell_signals['訊號等級'] == 'URGENT']
        high_signals = sell_signals[sell_signals['訊號等級'] == 'HIGH']

        msg = "🚨 <b>融券異常 - 賣訊警報</b> 🚨\n"
        msg += f"⚠️ 發現 {len(sell_signals)} 個賣訊，其中 {len(urgent_signals)} 個 URGENT\n\n"

        for _, row in urgent_signals.iterrows():
            msg += f"<b>🔴 {row['股票代號']}</b> - RSI: {row['RSI']}\n"
            msg += f"   現價: ${row['現股價']:.2f} | 融券增幅: {row['融券增幅%']}%\n"
            msg += f"   ⚠️ {row.get('風險警告', '主力做空訊號')}\n\n"

        self.send_message(msg, priority='urgent')

    def send_daily_summary(self, signals: pd.DataFrame):
        """發送每日摘要"""
        msg = "<b>📊 融資融券動能策略日報</b>\n"
        msg += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        buy_signals = signals[signals['訊號類型'] == 'BUY']
        sell_signals = signals[signals['訊號類型'] == 'SELL']

        msg += f"📈 買訊: {len(buy_signals)} 個\n"
        msg += f"📉 賣訊: {len(sell_signals)} 個\n"
        msg += f"📊 總計: {len(signals)} 個訊號\n\n"

        if not buy_signals.empty:
            top_buy = buy_signals[buy_signals['訊號等級'] == 'S級'].head(3)
            if not top_buy.empty:
                msg += "<b>🔥 TOP 3 買訊機會</b>\n"
                for _, row in top_buy.iterrows():
                    msg += f"  • {row['股票代號']}: ${row['現股價']:.2f} (預期 +{row['預期報酬%']}%)\n"
                msg += "\n"

        msg += "💡 詳細分析請查看 Google Sheets\n"
        msg += "⚠️ 記得嚴守停損規則！"

        self.send_message(msg, priority='normal')

    def test_notification(self):
        """測試通知功能"""
        test_messages = [
            {
                'text': '🧪 測試：普通優先級訊息（應該靜音）',
                'priority': 'normal'
            },
            {
                'text': '🔔 測試：高優先級訊息（應該有通知音）',
                'priority': 'high'
            },
            {
                'text': '🚨 測試：緊急優先級訊息（應該有通知音）',
                'priority': 'urgent'
            }
        ]

        logger.info("開始測試 Telegram 通知...", "telegram")
        for msg_info in test_messages:
            self.send_message(msg_info['text'], priority=msg_info['priority'])
            time.sleep(2)
        logger.info("測試完成！", "telegram")
