#!/usr/bin/env python3
"""
Google Drive 認証スクリプト（初回のみ実行）
drive.file スコープで認証し、gdrive_token.json を生成する

Usage: python3 Google_Drive/auth_gdrive.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    # client_secret_*.json を自動検出
    matches = list(SCRIPT_DIR.glob("client_secret_*.json"))
    if not matches:
        print("エラー: client_secret_*.json が Google_Drive/ フォルダに見つかりません。")
        print("Google Cloud Console からダウンロードしたJSONファイルをこのフォルダに保存してください。")
        return

    oauth_path = matches[0]
    token_path = SCRIPT_DIR / "gdrive_token.json"

    print(f"認証情報: {oauth_path.name}")
    flow = InstalledAppFlow.from_client_secrets_file(str(oauth_path), SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"認証完了。トークン保存: {token_path}")


if __name__ == "__main__":
    main()
