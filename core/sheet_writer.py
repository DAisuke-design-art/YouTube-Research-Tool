"""
Google Sheets 書き込みモジュール
サービスアカウント認証でスプレッドシートにデータを追記する
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# カラムマッピング: Tool内部名 → スプレッドシート日本語ヘッダー
COLUMN_MAP = {
    '調査日時': None,           # 実行時に動的生成
    '検索キーワード': None,     # 引数から取得
    'タイトル': 'title',
    'チャンネル名': 'channel_title',
    '登録者数': 'subscriber_count',
    '再生数': 'view_count',
    'GKスコア': 'gk_score',
    'URL': 'video_id',          # video_id → URL に変換
    '公開日': 'published_at',
    '動画時間(秒)': 'duration_sec',
    'いいね数': 'like_count',
    'コメント数': 'comment_count',
    'サムネイル': 'thumbnail',
}

SHEET_HEADERS = list(COLUMN_MAP.keys())


class SheetWriter:
    """Google Sheets への書き込みを担当するクラス"""

    def __init__(self, credentials_path: str, spreadsheet_id: str, sheet_name: str = "Sheet1"):
        """
        Args:
            credentials_path: サービスアカウントJSONキーファイルのパス
            spreadsheet_id: Google SpreadsheetのID
            sheet_name: 書き込み先のシート名
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.credentials_path = credentials_path
        self._client = None
        self._worksheet = None

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
            self._client = gspread.authorize(creds)
            spreadsheet = self._client.open_by_key(spreadsheet_id)
            try:
                self._worksheet = spreadsheet.worksheet(sheet_name)
            except Exception:
                # 日本語ロケール ("シート1") 等でシート名が異なる場合、最初のシートを使用
                self._worksheet = spreadsheet.get_worksheet(0)
                logger.info("シート '%s' が見つからないため、最初のシートを使用: '%s'",
                            sheet_name, self._worksheet.title)
            logger.info("Google Sheets 接続成功: %s (シート: %s)", spreadsheet_id, self._worksheet.title)
        except Exception as e:
            logger.warning("Google Sheets 接続失敗 (フォールバック: ローカルJSONのみ): %s", e)
            self._worksheet = None

    def _ensure_headers(self):
        """ヘッダー行が空の場合、自動的に挿入する"""
        if self._worksheet is None:
            return False

        try:
            row1 = self._worksheet.row_values(1)
            if not row1 or all(cell == "" for cell in row1):
                self._worksheet.update("A1", [SHEET_HEADERS])
                logger.info("ヘッダー行を自動作成しました")
            return True
        except Exception as e:
            logger.warning("ヘッダー確認/作成に失敗: %s", e)
            return False

    def append_results(self, df, keyword: str) -> bool:
        """
        DataFrameの内容をスプレッドシートに追記する

        Args:
            df: 検索結果のDataFrame (analyzer.pyの出力)
            keyword: 検索キーワード

        Returns:
            書き込み成功ならTrue、失敗ならFalse
        """
        if self._worksheet is None:
            logger.warning("Sheets未接続のため書き込みスキップ")
            return False

        if df.empty:
            logger.info("空のDataFrame: 書き込みスキップ")
            return True

        try:
            # ヘッダー確認・作成
            self._ensure_headers()

            # 現在の日時 (JST)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # DataFrame → 行データに変換
            rows = []
            for _, row in df.iterrows():
                sheet_row = []
                for header, field in COLUMN_MAP.items():
                    if header == '調査日時':
                        sheet_row.append(timestamp)
                    elif header == '検索キーワード':
                        sheet_row.append(keyword)
                    elif header == 'URL':
                        vid = row.get('video_id', '')
                        sheet_row.append(f"https://www.youtube.com/watch?v={vid}")
                    elif header == '公開日':
                        pub = str(row.get('published_at', ''))
                        sheet_row.append(pub[:10])  # YYYY-MM-DD のみ
                    elif header == 'サムネイル':
                        thumb_url = row.get('thumbnail', '')
                        sheet_row.append(f'=IMAGE("{thumb_url}")' if thumb_url else '')
                    else:
                        val = row.get(field, '')
                        # 数値型はそのまま、リスト型は文字列化
                        if isinstance(val, list):
                            val = ', '.join(str(v) for v in val)
                        sheet_row.append(val)
                rows.append(sheet_row)

            # 一括追記
            self._worksheet.append_rows(rows, value_input_option="USER_ENTERED")
            logger.info("Google Sheets に %d 行を追記しました (キーワード: %s)", len(rows), keyword)
            return True

        except Exception as e:
            logger.warning("Google Sheets 書き込みエラー: %s", e)
            return False


def create_sheet_writer():
    """
    環境変数からSheetWriterインスタンスを生成するファクトリ関数
    認証情報がない場合はNoneを返す
    """
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
    sheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")

    if not creds_path or not sheet_id:
        logger.info("GOOGLE_SERVICE_ACCOUNT_KEY / GOOGLE_SPREADSHEET_ID が未設定: Sheet書き込み無効")
        return None

    if not os.path.exists(creds_path):
        logger.warning("サービスアカウントキーファイルが見つかりません: %s", creds_path)
        return None

    return SheetWriter(creds_path, sheet_id)
