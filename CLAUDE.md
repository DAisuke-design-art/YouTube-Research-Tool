# YouTube Research Tool

必ず日本語で回答してください。

## リポジトリの目的

YouTube Data API v3を使ったリサーチツール。キーワード検索→動画分析→Excel出力→コメント抽出を一括で行う。

## 操作環境

ユーザーはAntigravity上のClaude Code（GUI）から操作する。非エンジニア前提。

## API仕様

ローカルサーバー起動後、以下のAPIが利用可能:

| エンドポイント | メソッド | 用途 |
|---|---|---|
| `/api/search?q=KW&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&videoType=any` | GET | キーワード検索 |
| `/api/export` | POST | 検索結果をExcelに出力（bodyにdata + keyword） |
| `/api/comments?videoId=VIDEO_ID` | GET | 動画コメント取得（最大2000件） |

## スキル一覧

| スキル | 呼び出し | 用途 |
|---|---|---|
| youtube-research | `/youtube-research` | キーワード検索→Excel出力→コメント抽出を一括自動実行 |

## セットアップ

1. `.env.example` をコピーして `.env` を作成
2. YouTube Data API v3のキーを `.env` に設定
3. `npm install` → `npm run dev` でサーバー起動
4. `http://localhost:3000` でGUIアクセス可能

## Googleドライブ連携

ユーザーが「Googleドライブの認証をして」と言ったら、以下を実行する:

```bash
python3 Google_Drive/auth_gdrive.py
```

→ ブラウザが開く → Googleアカウントでログイン → `Google_Drive/gdrive_token.json` が生成されて認証完了。

## 運用ルール

- `.env` ファイルはGitにコミットしない（APIキーを含むため）
- ポート3000が使用中の場合: `lsof -ti:3000 | xargs kill -9` で開放
