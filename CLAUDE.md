# YouTube Research Tool

必ず日本語で回答してください。

## リポジトリの目的

YouTube Data API v3を使ったリサーチツール。キーワード検索→動画分析→Excel出力→コメント抽出→市場マップ生成を、**Python単体スクリプト**で一括実行する。

## 操作環境

ユーザーはAntigravity上のClaude Code（GUI）から操作する。非エンジニア前提。

## Critical — 実行ルール

- **実行主体は `python3 youtube_research.py` のみ**
- **新規スクリプトの作成は完全禁止**。`run_research.py` `get_hit_videos.py` 等のラッパー・ヘルパーを作ってはならない
- **Next.jsサーバーは存在しない**。`npm run dev` `npm install` `curl http://localhost:3000/...` は全て禁止
- **`urllib` / `requests` / `curl` でローカルAPIを叩くコードを書くな**
- 機能に不満がある場合は `youtube_research.py` 自体を修正せよ

## スキル一覧

| スキル | 呼び出し | 用途 |
|---|---|---|
| youtube-research | `/youtube-research` | キーワード検索→Excel出力→コメント抽出→市場マップを一括自動実行 |

詳細は `.claude/skills/youtube-research/SKILL.md` を参照。

## セットアップ

1. `.env.example` をコピーして `.env` を作成
2. YouTube Data API v3のキーを `.env` に設定
3. Python依存パッケージをインストール: `pip3 install -r requirements.txt`
4. 実行: `python3 youtube_research.py --keywords "AI 資料作成"`

## Googleドライブ連携（任意）

ユーザーが「Googleドライブの認証をして」と言ったら、以下を実行する:

```bash
python3 Google_Drive/auth_gdrive.py
```

→ ブラウザが開く → Googleアカウントでログイン → `Google_Drive/gdrive_token.json` が生成されて認証完了。

## 運用ルール

- `.env` ファイルはGitにコミットしない（APIキーを含むため）
- 出力先は `./output/` 配下。スクリプトが `{メインKW}-Research-{YYYYMMDD}-time{HHMM}/` 形式で自動命名する
- 同日に何度実行しても別フォルダが生成され、既存結果を上書きしない
