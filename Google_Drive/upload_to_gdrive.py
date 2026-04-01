#!/usr/bin/env python3
"""
Google Drive アップローダー
output/ フォルダの内容をGoogleドライブにアップロードする

Usage: python3 Google_Drive/upload_to_gdrive.py <local_folder_path> [gdrive_folder_name]
例: python3 Google_Drive/upload_to_gdrive.py ./output research-data
"""

import os
import sys
import json
import mimetypes
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCRIPT_DIR = Path(__file__).parent
TOKEN_PATH = SCRIPT_DIR / "gdrive_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def load_credentials():
    if not TOKEN_PATH.exists():
        print("エラー: gdrive_token.json が見つかりません。")
        print("先に以下を実行して認証してください:")
        print("  python3 Google_Drive/auth_gdrive.py")
        sys.exit(1)

    with open(TOKEN_PATH) as f:
        d = json.load(f)

    creds = Credentials(
        token=d.get("access_token"),
        refresh_token=d.get("refresh_token"),
        token_uri=d.get("token_uri"),
        client_id=d.get("client_id"),
        client_secret=d.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def create_folder(service, name, parent_id=None):
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    print(f"  フォルダ作成: {name} (id: {folder['id']})")
    return folder["id"]


def upload_file(service, file_path, parent_id):
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    meta = {"name": file_path.name, "parents": [parent_id]}
    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
    f = service.files().create(body=meta, media_body=media, fields="id,name").execute()
    print(f"  アップロード: {file_path.name}")
    return f["id"]


def upload_folder(service, local_path, gdrive_folder_name, parent_id=None):
    folder_id = create_folder(service, gdrive_folder_name, parent_id)
    local = Path(local_path)
    for item in sorted(local.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_file() and item.suffix == ".xlsx":
            upload_file(service, item, folder_id)
        elif item.is_dir():
            upload_folder(service, item, item.name, folder_id)
    return folder_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 Google_Drive/upload_to_gdrive.py <local_folder_path> [gdrive_folder_name]")
        sys.exit(1)

    local_path = sys.argv[1]
    gdrive_name = sys.argv[2] if len(sys.argv) > 2 else Path(local_path).name

    if not os.path.exists(local_path):
        print(f"エラー: {local_path} が見つからない")
        sys.exit(1)

    print(f"認証情報を読み込み中...")
    creds = load_credentials()
    service = build("drive", "v3", credentials=creds)

    print(f"アップロード開始: {local_path} → GoogleDrive/{gdrive_name}")
    folder_id = upload_folder(service, local_path, gdrive_name)
    print(f"\n完了。GoogleDriveフォルダID: {folder_id}")
    print(f"URL: https://drive.google.com/drive/folders/{folder_id}")


if __name__ == "__main__":
    main()
