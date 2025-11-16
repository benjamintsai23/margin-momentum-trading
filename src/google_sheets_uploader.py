"""
Google Sheets 上報模組 - 將分析結果上報到 Google Sheets
"""
import gspread
import pandas as pd
from typing import Optional
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from src.config import Config
from src.utils.logger import Logger

logger = Logger()


class GoogleSheetsUploader:
    """Google Sheets 上報管理器"""

    def __init__(self):
        """初始化 Google Sheets 連接"""
        self.sheet_id = Config.GOOGLE_SHEETS_ID
        self._authenticate()

    def _authenticate(self):
        """驗證 Google API"""
        try:
            scope = Config.GOOGLE_SCOPE
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                Config.CREDENTIAL_FILE, scope
            )
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            logger.info("✅ Google Sheets 連接成功", "sheets")
        except FileNotFoundError:
            logger.error(f"找不到認證文件: {Config.CREDENTIAL_FILE}", "sheets")
            raise
        except Exception as e:
            logger.error(f"Google Sheets 驗證失敗: {e}", "sheets")
            raise

    def upload_signals(self, signals: pd.DataFrame, sheet_name: str = "融資融券訊號"):
        """
        上報買賣訊號到 Google Sheets

        Args:
            signals: 訊號 DataFrame
            sheet_name: Sheet 名稱
        """
        try:
            if signals.empty:
                logger.info("無訊號需要上報", "sheets")
                return

            # 取得或建立工作表
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"工作表 '{sheet_name}' 不存在，建立新表", "sheets")
                worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

            # 清空既有資料（保留標題）
            if worksheet.row_count > 1:
                worksheet.delete_rows(2, worksheet.row_count)

            # 寫入資料
            values = [signals.columns.tolist()] + signals.values.tolist()
            worksheet.update('A1', values)

            logger.info(f"成功上報 {len(signals)} 個訊號到 Google Sheets", "sheets")

        except Exception as e:
            logger.error(f"Google Sheets 上報失敗: {e}", "sheets")
            raise

    def upload_portfolio(self, portfolio: pd.DataFrame, sheet_name: str = "持倉組合"):
        """
        上報投資組合到 Google Sheets

        Args:
            portfolio: 投資組合 DataFrame
            sheet_name: Sheet 名稱
        """
        try:
            # 取得或建立工作表
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"工作表 '{sheet_name}' 不存在，建立新表", "sheets")
                worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=15)

            # 清空既有資料
            if worksheet.row_count > 1:
                worksheet.delete_rows(2, worksheet.row_count)

            # 寫入資料
            values = [portfolio.columns.tolist()] + portfolio.values.tolist()
            worksheet.update('A1', values)

            logger.info(f"成功上報投資組合到 Google Sheets", "sheets")

        except Exception as e:
            logger.error(f"Google Sheets 投資組合上報失敗: {e}", "sheets")

    def upload_backtest_results(self, results: dict, sheet_name: str = "回測結果"):
        """
        上報回測結果到 Google Sheets

        Args:
            results: 回測結果字典
            sheet_name: Sheet 名稱
        """
        try:
            # 轉換為 DataFrame
            df = pd.DataFrame([results])

            # 取得或建立工作表
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"工作表 '{sheet_name}' 不存在，建立新表", "sheets")
                worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=15)

            # 寫入資料
            values = [df.columns.tolist()] + df.values.tolist()
            worksheet.update('A1', values)

            logger.info(f"成功上報回測結果到 Google Sheets", "sheets")

        except Exception as e:
            logger.error(f"Google Sheets 回測結果上報失敗: {e}", "sheets")

    def append_signals(self, signals: pd.DataFrame, sheet_name: str = "融資融券訊號"):
        """
        追加訊號到 Google Sheets（不覆蓋既有資料）

        Args:
            signals: 訊號 DataFrame
            sheet_name: Sheet 名稱
        """
        try:
            if signals.empty:
                logger.info("無訊號需要上報", "sheets")
                return

            # 取得或建立工作表
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"工作表 '{sheet_name}' 不存在，建立新表", "sheets")
                worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

            # 如果工作表為空，先寫入標題
            if len(worksheet.get_all_values()) == 0:
                worksheet.append_row(signals.columns.tolist())

            # 追加資料
            for _, row in signals.iterrows():
                worksheet.append_row(row.tolist())

            logger.info(f"成功追加 {len(signals)} 個訊號到 Google Sheets", "sheets")

        except Exception as e:
            logger.error(f"Google Sheets 追加訊號失敗: {e}", "sheets")

    def get_signals(self, sheet_name: str = "融資融券訊號") -> pd.DataFrame:
        """
        從 Google Sheets 讀取訊號資料

        Args:
            sheet_name: Sheet 名稱

        Returns:
            訊號 DataFrame
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)

        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"工作表 '{sheet_name}' 不存在", "sheets")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Google Sheets 讀取失敗: {e}", "sheets")
            return pd.DataFrame()

    def create_summary(self, signals: pd.DataFrame) -> dict:
        """
        建立摘要統計

        Returns:
            統計結果字典
        """
        if signals.empty:
            return {}

        buy_signals = signals[signals['訊號類型'] == 'BUY']
        sell_signals = signals[signals['訊號類型'] == 'SELL']

        summary = {
            '分析日期': datetime.now().strftime('%Y-%m-%d'),
            '分析時間': datetime.now().strftime('%H:%M:%S'),
            '總訊號數': len(signals),
            '買訊數': len(buy_signals),
            '賣訊數': len(sell_signals),
            'S級訊號': len(buy_signals[buy_signals['訊號等級'] == 'S級']) if not buy_signals.empty else 0,
            'A級訊號': len(buy_signals[buy_signals['訊號等級'] == 'A級']) if not buy_signals.empty else 0,
            '緊急賣訊': len(sell_signals[sell_signals['訊號等級'] == 'URGENT']) if not sell_signals.empty else 0,
        }

        return summary
