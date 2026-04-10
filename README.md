# YouTube Research Tool

YouTube Data API v3 を活用し、キーワードから動画データを一括リサーチ・Excel出力・コメント抽出・市場マップ生成までを**Python単体スクリプト**で実行するツールです。

## 特徴
- Python単体で動作（Next.jsサーバー不要）
- YouTube Data API v3 による高精度なキーワード検索
- 再生数・エンゲージメント率・日次平均再生・V/S比を自動算出
- Excel(.xlsx) 出力（行1固定・赤ヘッダーで視認性確保）
- 上位ヒット動画のコメント自動抽出（JSON出力）
- 市場マップMD（`market-map.md`）の自動生成
- AntigravityなどのAIアシスタントから `/youtube-research` で一発実行

---

## ⚡ 超高速セットアップ (プログラミング未経験者・非エンジニア向け)

このツールは、**AI（Antigravity等）におまかせ**で動かすことができます。

### Step 1: ツール一式をダウンロード
1. この画面の右上にある緑色の **`<> Code ▾`** ボタンをクリック
2. 一番下の **`Download ZIP`** をクリック
3. ダウンロードされたZIPファイルを解凍

### Step 2: YouTube Data API v3 キーの取得
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスし、新しいプロジェクトを作成
2. 「APIとサービス」 > 「ライブラリ」から **YouTube Data API v3** を検索し、有効化
3. 「認証情報」タブから「認証情報を作成」>「APIキー」を選択し、キーをコピー

### Step 3: 環境変数の準備
⚠️ **APIキーをAIのチャット欄に直接貼り付けないでください。**

1. Step 1 で解凍したフォルダを開く
2. `.env.example` をコピーして `.env` にリネーム
3. `.env` をメモ帳などで開き、`YOUTUBE_API_KEY=` の右側にAPIキーを貼り付け保存
   - 💡 複数のAPIキー設定でクォータ超過時の自動切替が可能。`YOUTUBE_API_KEY_1=`, `YOUTUBE_API_KEY_2=` のコメントを外して記入

### Step 4: AI（Antigravity）への丸投げ
1. Antigravity を起動
2. 解凍フォルダをAntigravity画面にドラッグ＆ドロップ
3. 以下のプロンプトをそのまま送信:

> 「このプロジェクトの依存パッケージをインストールして（`pip3 install -r requirements.txt`）、次に `/youtube-research` でリサーチを開始してください。」

**🎉 完了です。** AIがパッケージをインストールし、`/youtube-research` スキルがキーワード入力から結果出力までを自動実行します。

出力先: `./output/{メインKW}-Research-{YYYYMMDD}-time{HHMM}/`

---

## 手動セットアップ（エンジニア向け）

### 1. 環境変数の設定

```bash
cp .env.example .env
```

**.env**
```
YOUTUBE_API_KEY=your_api_key_here
```

### 2. Python依存パッケージのインストール

```bash
pip3 install -r requirements.txt
```

必要パッケージ: `requests`, `openpyxl`, `python-dotenv`

### 3. 実行

対話モード（キーワードを対話で入力）:
```bash
python3 youtube_research.py
```

AI実行モード（キーワード指定で完走）:
```bash
python3 youtube_research.py --keywords "AI 資料作成,Claude 使い方" --market-map
```

主要オプション:
- `--keywords "KW1,KW2"` — カンマ区切りキーワード
- `--period 6` — 検索期間（月数、デフォルト6）
- `--type normal` — 動画タイプ: any / normal / shorts（デフォルト: normal）
- `--no-comments` — コメント取得をスキップ
- `--market-map` — 市場マップMD (`market-map.md`) を自動生成
- `--output-dir ./output` — 出力先（デフォルト: `./output`、スクリプトが日時サフィックスを自動付与）

---

## 出力物

実行後、`./output/{メインKW}-Research-{YYYYMMDD}-time{HHMM}/` 配下に以下が生成されます:

| ファイル | 内容 |
|---|---|
| `YTR_{KW}_{日付}_{連番}.xlsx` | キーワード別検索結果（再生数・VS比・尺等の全メトリクス） |
| `YTR_{KW}_{日付}_{連番}_comments.json` | ヒット動画のコメント抽出結果 |
| `market-map.md` | KW別上位10本の市場マップ（`--market-map`指定時） |

---

## ライセンス
This project is licensed under the MIT License - see the LICENSE file for details.
