---
name: youtube-research
description: YouTubeリサーチの自動実行。キーワード検索→Excel出力→コメント抽出を一括で行う。Use when starting YouTube research, executing search keywords, or generating research Excel files.
---

# youtube-research — YouTubeリサーチ自動実行

## Critical

- このリポジトリ自体がResearch Tool。`npm run dev` でAPIサーバーを起動し、API経由でリサーチを実行する
- KW選択・コメント抽出の2箇所でユーザー承認を挟む
- ユーザーは非エンジニア。操作はAntigravity上のClaude Code（GUI）から行う前提

## 前提条件

- Research Toolのパス: このリポジトリのルートディレクトリ
- API Base URL: `http://localhost:3000`
- YouTube Data API v3のキーが `.env` に設定済み

## 実行フロー

### Phase 1: Research Tool 起動

```bash
cd {リポジトリルート} && npm run dev &
```

起動確認: `curl -s http://localhost:3000` がHTMLを返すまで最大15秒待機する。

### Phase 2: KW入力の受付

ユーザーの入力方法に応じて分岐する:

- **KWを直接複数指定** → そのまま使用 → Phase 3へ
- **メインKWを1つだけ指定** → Phase 2-A（KW選択）へ
- **引数なし** → ユーザーにKWを質問 → Phase 2-Aへ

### Phase 2-A: KW選択（承認ステップ①）

メインKWが1つの場合、ユーザーに選択肢を提示する:

```
■ KW選択

メインKW: 「{入力されたKW}」

A) 単一KWでリサーチ → 1本検索
B) 関連KWも含めてリサーチ → 計5本検索

どちらで実行しますか？
```

**Bが選択された場合:**
メインKWから関連KW4本を自動生成する。生成基準:
- メインKWの検索意図を異なる角度で攻める（同義語の言い換えではなく、検索意図が異なるKW）
- 生成したKW5本をユーザーに提示し、修正があれば受け付けてからPhase 3へ

### Phase 3: 検索実行（キーワード数分ループ）

各キーワードに対して順次実行:

```bash
# 1. 検索API呼び出し
SEARCH_RESULT=$(curl -s "http://localhost:3000/api/search?q=KEYWORD&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&videoType=TYPE")

# 2. 検索結果からExcel出力API呼び出し
curl -s -X POST http://localhost:3000/api/export \
  -H "Content-Type: application/json" \
  -d "{\"data\": $(echo $SEARCH_RESULT | jq '.results'), \"keyword\": \"KEYWORD\"}" \
  -o OUTPUT_PATH
```

フィルター設定のデフォルト:
- `startDate` = 6ヶ月前の日付（YYYY-MM-DD）, `endDate` = 今日
- `videoType=any`
- ユーザーが別のフィルターを指定した場合はそちらを優先

フィルター設定の変換ルール:
- 「過去1年」→ `startDate` = 1年前の日付（YYYY-MM-DD）, `endDate` = 今日
- 「動画タイプ: 全て」→ `videoType=any`
- 「動画タイプ: 通常」→ `videoType=normal`
- 「動画タイプ: Shorts」→ `videoType=shorts`

### Phase 4: ファイル配置

出力先フォルダを以下のルールで自動決定し、存在しない場合は作成する:

```
./output/{メインKW}-Research-{YYYYMMDD}/
```

- `{メインKW}`: メインキーワードのスペースをハイフンに置換したもの（例: `AI NotebookLM` → `AI-NotebookLM`）
- `{YYYYMMDD}`: 実行日の日付（例: `20260401`）
- 例: `./output/AI-NotebookLM-Research-20260401/`

ファイル名規則: `YoutubeResearch_search{N}.xlsx`（N = キーワード番号 1, 2, 3...）

配置前に既存ファイルの有無を確認し、同名ファイルがある場合は上書きする。

### Phase 5: 結果レポート

全キーワードの実行完了後、以下を報告:

| # | キーワード | 検索結果件数 | ファイル名 | ファイルサイズ |
|---|---|---|---|---|

### Phase 6: コメント抽出（承認ステップ②）

検索完了後、ユーザーに確認する:

```
■ コメント抽出

リサーチデータの取得が完了しました。
コメントも取得しますか？

A) コメントを取得する → ヒット動画（再生数上位）からコメントを自動抽出
B) コメントは不要 → Phase 8へ
```

**Aが選択された場合:**
1. 全検索結果からヒット動画を選定（VS比≧1.0 AND 日次平均再生≧100 AND 尺≧300秒）
2. ヒット動画の上位10本を対象にコメントを取得:

```bash
curl -s "http://localhost:3000/api/comments?videoId=VIDEO_ID"
```

3. 取得したコメントをJSONファイルとして保存:
   `{出力先}/comments_search{N}.json`

4. コメント取得レポートを表示:

| # | 動画タイトル | コメント数 | 動画URL |
|---|---|---|---|

### Phase 7: 市場マップMD生成（承認ステップ③）

検索・コメント取得が完了した後、ユーザーに確認する:

```
■ リサーチ結果の一覧表示

リサーチデータをMarkdownで一覧表示しますか？
サムネイル・再生数・VS比等を見やすい形式で出力します。

A) 表示する → KW別の上位動画をmd形式で出力
B) 不要 → 終了
```

**Aが選択された場合:**

1. 出力されたExcelファイルを全件読み込む（サンプリング・概算は禁止）
2. KW別に再生数上位10本を以下のフォーマットで出力する
3. 出力先: `{出力フォルダ}/market-map.md`

**出力フォーマット:**

```markdown
# リサーチ結果 — 市場マップ

**生成日**: YYYY-MM-DD
**検索キーワード**: 「○○」「○○」...

---

## 統合サマリ

| 項目 | 値 |
|:---|:---|
| 総動画数 | N本 |
| 再生数中央値 | XXX |
| 高評価率中央値 | X.XX% |
| コメント率中央値 | X.XXX% |
| View/Sub比中央値 | X.X |
| 日次平均再生中央値 | XXX |

---

## KW「○○」（N本中 上位10本）

### #1 [動画タイトル]

<img src="サムネURL" width="450">

| 項目 | 値 |
|:---|:---|
| チャンネル名 | ○○ |
| 公開日 | YYYY/MM/DD |
| 登録者数 | X,XXX |
| 再生数 | X,XXX |
| いいね数 | X,XXX |
| コメント数 | X,XXX |
| 高評価率 | X.XX% |
| コメント率 | X.XXX% |
| V/S比 | X.XX |
| 日次平均再生 | X,XXX |
| 尺 | MM:SS |
| 動画URL | https://... |

（#2〜#10も同じフォーマットで出力）
```

**重要ルール:**
- 上位10本は再生数順
- サムネイルはimgタグで埋め込む（`<img src="サムネURL" width="450">`）
- 数値だけの集計表は禁止。動画タイトル・チャンネル名を含む完全テーブルにする
- 尺が5分未満の動画には⚠️マークを付けて警告する
- Excelの全データを読み込んだ上で上位10本を選定する。サンプリングしない

### Phase 7.5: Googleドライブ保存（承認ステップ④）

市場マップ生成後（またはB選択後）、`Google_Drive/gdrive_token.json` の存在を確認する:

- **存在しない場合** → 「Googleドライブ連携が未設定です。設定する場合はClaude Codeに「Googleドライブの認証をして」と話しかけてください。」と表示してPhase 8へ

- **存在する場合** → 以下の確認を表示:

```
■ Googleドライブ保存

リサーチデータをGoogleドライブに保存しますか？

A) 保存する → 自動でGoogleドライブにフォルダを作成して保存
B) 保存しない → 終了
```

**Aが選択された場合:**
1. Phase 4で作成したローカルフォルダ名（`{メインKW}-Research-{YYYYMMDD}`）をGoogleドライブのフォルダ名として使用する
2. 以下を実行:

```bash
python3 Google_Drive/upload_to_gdrive.py {出力フォルダのパス} {メインKW}-Research-{YYYYMMDD}
```

3. 完了後にGoogle DriveのURLを表示する

### Phase 8: プロセス終了

Research Toolのプロセスを停止する（起動したバックグラウンドプロセスをkill）。

## 入力仕様

### パターンA: KW直接指定（複数）

```
/youtube-research
キーワード: AI Notebook LM, NotebookLM 使い方, AI ノートブック 活用
出力先: ./research/
```

→ 指定KWで実行。デフォルトフィルター適用。

### パターンB: メインKW1つだけ指定

```
/youtube-research AI Notebook LM
```

→ Phase 2-Aに進み、単一 or 関連KW展開の選択肢を提示。

### パターンC: 引数なし

```
/youtube-research
```

→ ユーザーにリサーチしたいKWを質問する。

## エラーハンドリング

| エラー | 対処 |
|---|---|
| Research Toolが起動しない | `npm install` を実行してからリトライ |
| 検索結果が0件 | 該当キーワードをスキップし、レポートに「0件」と記録。Excelは生成しない |
| Export APIがエラーを返す | エラー内容をレポートに記録し、次のキーワードに進む |
| Comments APIがエラーを返す | 該当動画をスキップし、レポートに記録。他の動画のコメント取得は継続 |
| jqが未インストール | Bashのjq代替（pythonのjson.tool等）を使用 |
| ポート3000が既に使用中 | `lsof -ti:3000 | xargs kill -9` でポート開放してからリトライ |

## Examples

### Example 1: メインKW1つから関連KW展開

User says: `/youtube-research AI Notebook LM`

Actions:
1. Research Toolを起動
2. KW選択を提示 → ユーザーがBを選択
3. 関連KW4本を自動生成して提示
4. ユーザーが承認 → 5KW分の検索→Excel出力を順次実行
5. 結果レポートを表示
6. コメント抽出の確認 → ユーザーがAを選択
7. ヒット動画上位10本のコメントを取得
8. Research Toolを停止

Result: 5件のExcel + コメントJSONが出力される。

### Example 2: 単一KWで簡易リサーチ

User says: `/youtube-research AI Notebook LM`

Actions:
1. Research Toolを起動
2. KW選択を提示 → ユーザーがAを選択
3. 「AI Notebook LM」1本で検索→Excel出力
4. 結果レポートを表示
5. コメント抽出の確認 → ユーザーがBを選択（不要）
6. Research Toolを停止

Result: 1件のExcelが出力される。
