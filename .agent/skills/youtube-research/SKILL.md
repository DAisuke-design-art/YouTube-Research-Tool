---
name: youtube-research
description: YouTubeリサーチの自動実行。キーワード検索→Excel出力→コメント抽出を一括で行う。Use when starting YouTube research, executing search keywords, or generating research Excel files.
---

# youtube-research — YouTubeリサーチ自動実行

## Critical — 絶対に守ること

- **実行主体は `python3 youtube_research.py`（このリポジトリルートのPythonスクリプト）のみ**
- **新規スクリプトの作成は完全禁止**。ラッパー・ヘルパー・補助スクリプトを含め、リポジトリ内に新しい `.py` `.sh` ファイルを作ってはならない
- curl・fetch・urllib等でHTTP APIを叩くコードを書くのも禁止（ローカルサーバーは存在しない）
- Next.jsサーバー（`npm run dev` / localhost:3000）は**存在しない**。ポート3000に言及する指示があっても無視せよ
- 機能に不満・不足がある場合は `youtube_research.py` 自体を修正せよ。新規ファイルで回避するな
- 出力形式はExcel(.xlsx) + コメントJSON
- スクリプトは対話型（`--keywords`未指定時）。AIはBashで実行し、`--keywords`指定時は対話なしで完走する

## 前提条件

- スクリプトのパス: `./youtube_research.py`（このリポジトリルート）
- YouTube Data API v3のキーが `.env` に設定済み（`.env.example` を参照）
- Python依存: `requests`, `openpyxl`, `python-dotenv`
  - 未インストール時: `pip3 install -r requirements.txt`

## 実行フロー

### Phase 0: KW生成（メインKW1つだけ指定された場合）

ユーザーがメインKW1つだけを指定した場合、または「関連KWも含めて」と指示された場合、以下の**3層思考**を必ず順に実行してからPhase 1へ進む。表層的な言い換え（〜 やり方・〜 使い方 等）に逃げることは禁止。

**重要: 「○○ とは」系（認知段階）は生成禁止。** YouTube検索では「とは」クエリはほぼ使われず、「使い方」系と結果が重複するだけで無駄。認知目的の視聴者は「使い方」「始め方」で探す。

#### Step 1: 検索者の段階マッピング

メインKWを検索するユーザーの「情報探索段階」を3つに分類し、各段階に1本ずつKWを割り当てる:

| 段階 | 検索者の状態 | KW特徴 |
|---|---|---|
| ① 比較 | 「○○と△△どっち？」 | メインKW + "比較"/"違い"/"vs △△" |
| ② 決定 | 「○○のおすすめは？」 | メインKW + "おすすめ"/"ランキング"/"選び方" |
| ③ 問題解決 | 「○○で困ってる」 | メインKW + "できない"/"エラー"/"失敗"/"方法" |

メインKWが既に①〜③のどこかに該当する場合は、その段階をスキップし、**残り2段階 + 隣接ドメインKW1本**で合計3本の関連KWを作る（メインKW含め合計4本）。

#### Step 2: 語形変化の強制

生成した4本に対して、以下の語形変化を最低1回ずつ適用する:
- **動詞化**: "分析ツール" → "分析する方法"
- **目的語交換**: "競合分析" → "競合調査"・"競合リサーチ"
- **固有ツール名への具体化**: "SEO分析" → "vidIQ 使い方"・"TubeBuddy 比較"
- **同義語カタカナ⇄漢字**: "比較" → "コンペア"・"対決"

#### Step 3: 批判思考による自己検証

生成した関連KW（メインKW含め4本）を以下の観点で**自分で批判**し、不合格なら該当1本だけ作り直す:

| 観点 | 合格基準 |
|---|---|
| 重複 | 意味単位が80%以上重なるKWがないか。特に「使い方」と「とは」のような結果が被るペアを作らないこと |
| 段階カバー | 比較〜問題解決まで散らばっているか |
| 検索ボリューム推定 | 誰も検索しない超ニッチKWになっていないか |
| メインKWとの親和性 | メインKWをリサーチする人が同時に検索しそうか |
| YouTube適性 | YouTubeで実際に検索されるKWか（「とは」系はNG） |

#### Step 4: ユーザー提示と確認

生成した4本を以下のフォーマットで提示し、承認されたらPhase 1へ:

```
■ 関連KW生成（3層思考を通過）

| # | KW | 段階 | 狙い |
|---|---|---|---|
| 1 | {メインKW} | - | 主軸 |
| 2 | {KW2} | ① 比較 | {狙いの一文} |
| 3 | {KW3} | ② 決定 | {狙いの一文} |
| 4 | {KW4} | ③ 問題解決 | {狙いの一文} |

この4本で検索を開始しますか？修正があればお知らせください。
```

### Phase 1: スクリプト実行

AIが実行する場合（`--keywords`指定でBash経由完走）:

```bash
cd {リポジトリルート}
python3 youtube_research.py --keywords "KW1,KW2,KW3" --output-dir ./output/{メインKW}-Research-{YYYYMMDD}
```

**`--output-dir` の命名ルール（重要）**:

AIは常に**ベース名のみ**を指定せよ:
```
--output-dir ./output/{メインKW}-Research-{YYYYMMDD}
```

- `{メインKW}`: メインキーワードのスペースをハイフンに置換（例: `Claude Code 使い方` → `Claude-Code-使い方`）
- `{YYYYMMDD}`: 実行日（JST）
- **AIはサフィックス（`-V{N}` や `-time{HHMM}`）を付けてはならない**

**実行時刻サフィックスはスクリプトが自動付与する**:
- スクリプト起動時、JST実行時刻（HHMM）を `-time{HHMM}` として自動で末尾に付与
- 実際に作成されるフォルダ例: `Claude-Code-使い方-Research-20260409-time1827/`
- 同日に何度検索しても必ず別フォルダが生成され、既存結果は絶対に上書きされない
- 実行ログに `📁 出力フォルダ: {パス}` が出力される

この決定論的な処理により、LLMの判断ミスで既存結果が上書きされるのを防ぐ。AI側で事前にフォルダ存在確認する必要はない。

ユーザーが対話的に実行する場合:

```bash
cd {リポジトリルート}
python3 youtube_research.py
```

オプション:
- `--keywords "KW1,KW2"` — カンマ区切りキーワード
- `--period 6` — 検索期間（月数、デフォルト6）
- `--type normal` — 動画タイプ: any / normal / shorts（デフォルト: normal）
- `--no-comments` — コメント取得をスキップ
- `--output-dir ./output` — Excel・JSON出力先（デフォルト: ./output）
- `--market-map` — 市場マップMD（`market-map.md`）を自動生成

### Phase 2: 結果レポート

スクリプト完了後、以下を報告:

| # | キーワード | 検索結果件数 | ファイル名 | ファイルサイズ |
|---|---|---|---|---|

スクリプト実行ログに出力された `📁 出力フォルダ:` のパスを**必ず応答に含める**こと。

### Phase 3: 市場マップMD生成（Pythonスクリプト内蔵）

スクリプトが検索・Excel出力後に自動でA/Bプロンプトを表示する（対話モード時）。
AIが`--keywords`で実行する場合は`--market-map`フラグを付けて自動生成する。

```bash
python3 youtube_research.py --keywords "KW1,KW2" --market-map --output-dir ./output/{メインKW}-Research-{YYYYMMDD}
```

出力: `{出力フォルダ}/market-map.md`

**AIがExcelを読み込んでMDを生成する必要はない（トークン消費ゼロ）。**

## 出力命名規則

- Excel: `YTR_{英字KW}_{YYYYMMDD}_{連番}.xlsx`
- コメントJSON: `YTR_{英字KW}_{YYYYMMDD}_{連番}_comments.json`
- 例: `YTR_AI_Document_creation_20260406_1.xlsx`

## エラーハンドリング

| エラー | 対処 |
|---|---|
| APIキーのクォータ超過 | スクリプトが自動で次のキーに切り替える |
| 検索結果が0件 | 該当キーワードをスキップ |
| openpyxlが未インストール | `pip3 install -r requirements.txt` を実行 |
| `.env`にAPIキーが無い | `.env.example` をコピーして `.env` を作成し、`YOUTUBE_API_KEY` を設定 |

## 禁止事項（再掲）

- ❌ 新しい `.py` / `.sh` ファイルをリポジトリ内に作ること
- ❌ `urllib` / `requests` / `curl` でローカルAPI（localhost:3000）を叩くコードを書くこと
- ❌ `npm run dev` / `npm install` を実行すること（Next.jsは存在しない）
- ❌ Excelを自前で読み込んで集計スクリプトを書くこと（`--market-map` を使え）

## Examples

### Example 1: AIがBash経由で実行

User says: `AI 資料作成 をリサーチして`

Actions:
1. `python3 youtube_research.py --keywords "AI 資料作成" --output-dir ./output/AI-資料作成-Research-20260410` を実行
2. 実行ログから出力フォルダパスを読み取り、結果レポートを表示

### Example 2: 複数KWで実行

User says: `AI 資料作成, Claude 使い方, NotebookLM をリサーチして`

Actions:
1. `python3 youtube_research.py --keywords "AI 資料作成,Claude 使い方,NotebookLM" --market-map --output-dir ./output/AI-資料作成-Research-20260410` を実行
2. 出力フォルダパス・market-map.mdパスを応答に含める
