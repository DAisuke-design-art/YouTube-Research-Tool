---
name: skill-standards
description: Skill作成・変更時の品質基準（憲法）。Anthropic公式ガイド「The Complete Guide to Building Skills for Claude」に基づき、frontmatter要件、instructions構造、Progressive Disclosure、テスト戦略を定義する。Use when creating, editing, reviewing, or auditing any Skill file (SKILL.md).
---

# Skill Standards — スキル品質憲法

## 概要

本スキルは `.agent/skills/` 配下の全スキルに対する **品質基準（憲法）** を定義する。
すべてのSkill作成・変更は、本基準に準拠しなければならない。

詳細な根拠は `references/guide-ja.md`（Anthropic公式ガイド日本語翻訳）を参照せよ。

---

## 絶対原則（10箇条）

### 1. `name` は kebab-case 必須
- スペース・大文字・アンダースコア禁止
- フォルダ名と一致させること
- ✅ `my-skill-name` / ❌ `My Skill Name` / ❌ `my_skill_name`

### 2. `description` は WHAT + WHEN を含む
- **何をするか (WHAT)** と **いつ使うか (WHEN)** の両方を含めること
- トリガーフレーズ（ユーザーが言いそうな具体的なフレーズ）を記載
- 1024文字以内
- ✅ `映像言語の専門辞書。Use when selecting Shot Scale or Camera Angle for a scene.`
- ❌ `映像言語の専門辞書。`（トリガーなし）

### 3. XMLタグ禁止
- frontmatter に `<` `>` を含めてはならない（セキュリティ制約）

### 4. 予約語禁止
- `name` に "claude" / "anthropic" を含めてはならない

### 5. SKILL.md は 5000語以下
- 超える場合は `references/` ディレクトリに詳細を分割
- これは Progressive Disclosure 第3層の活用に該当する

### 6. Instructions は具体的・行動可能
- ❌ 抽象的: `データを適切に検証せよ`
- ✅ 具体的: `CRITICAL: create_project 呼び出し前に以下を確認: プロジェクト名が空でない / チームメンバーが1人以上`

### 7. 重要な指示はファイル上部に配置
- Claudeは長い指示の途中で迷うことがある
- `## Important` / `## Critical` ヘッダーを使用
- 必要に応じて重要なポイントを繰り返す

### 8. Examples セクション推奨
- 具体的なユーザー発話例とそれに対するActions/Resultを記載
- 形式: `User says: "..."` → `Actions:` → `Result:`

### 9. Troubleshooting セクション推奨
- よくある誤用パターンを `症状 → 原因 → 対処` の3段構成で記載

### 10. 新規Skill作成時は本ガイドを参照
- 作成前に `references/guide-ja.md` を確認し、構造・要件の準拠を検証すること

### 11. ネガティブプロンプト制限法
AIへの指示（Skill、GEMプロンプト、台本DIRECTIVE等）において、**「禁止」は最後の手段**とせよ。
- **11-1. ポジティブ定義第一原則**: `禁止`/`Ban`/`Negative`/`NG` を記述する前に、必ず「存在すべきもの」のポジティブ定義で代替可能か検証せよ。代替可能な場合はポジティブ定義に置換すること
- **11-2. バイアス語汚染禁止**: AIの学習データで支配的な概念（例: 鰻=蒲焼、寿司=一口サイズ）に紐づくワードを、**禁止目的であっても**プロンプトに記述することを禁止する。代わりにメタファー完全置換（`prompt-engineering-principles` 原則11）を適用せよ
- **11-3. Negative Prompt許可範囲**: Negative Promptの使用は、**画風・技法の排除のみ**に限定する。物体の形状・食感・歴史的事物に関するNegative Promptは全て禁止し、ポジティブ定義に置換せよ
- **11-4. サニタイズテーブル設計**: 汚染トークンの一覧テーブルは「置換元→置換先」の変換テーブルとして記述し、禁止語が単独で出現しない構造にせよ

---

## Progressive Disclosure（3層構造）

| 層 | 内容 | ロードタイミング |
|---|---|---|
| 第1層 | YAML frontmatter (name, description) | 常時（システムプロンプト） |
| 第2層 | SKILL.md 本文 | スキルが関連すると判断された時 |
| 第3層 | `references/` 内のファイル | 必要に応じて読み込み |

---

## 新規Skill作成チェックリスト

| # | チェック項目 | □ |
|---|------------|---|
| 1 | フォルダ名が kebab-case か？ | □ |
| 2 | `SKILL.md` が正確にこの名前か？（大文字小文字厳密） | □ |
| 3 | frontmatter に `---` デリミタがあるか？ | □ |
| 4 | `name` が kebab-case でフォルダ名と一致しているか？ | □ |
| 5 | `description` に WHAT + WHEN（トリガーフレーズ）が含まれているか？ | □ |
| 6 | XMLタグ (`< >`) が frontmatter に含まれていないか？ | □ |
| 7 | Instructions が具体的・行動可能か？ | □ |
| 8 | SKILL.md が 5000語以下か？ | □ |
| 9 | Examples セクションがあるか？ | □ |
| 10 | Troubleshooting セクションがあるか？ | □ |
| 11 | `references/` に分割すべき詳細情報がないか？ | □ |

---

## 既存Skill変更チェックリスト

| # | チェック項目 | □ |
|---|------------|---|
| 1 | 変更後も `name` が kebab-case を維持しているか？ | □ |
| 2 | 変更後も `description` にトリガーフレーズが含まれているか？ | □ |
| 3 | 変更後も SKILL.md が 5000語以下か？ | □ |
| 4 | 変更後も Examples / Troubleshooting が正確か？ | □ |

---

## Examples

### Example 1: 新規Skillの作成
User says: 「新しいスキルを作りたい」
Actions:
1. 本スキルの「新規Skill作成チェックリスト」を確認
2. `references/guide-ja.md` で詳細な構造要件を参照
3. kebab-case フォルダ名で作成開始
4. frontmatter に name + description (WHAT + WHEN) を記載
5. Instructions → Examples → Troubleshooting の順にセクションを構築
Result: ガイド準拠のSKILL.mdが完成

### Example 2: 既存Skillの監査
User says: 「スキルがガイドに準拠しているか確認して」
Actions:
1. 対象スキルの frontmatter を確認（name kebab-case, description trigger phrases）
2. 語数チェック（5000語以下）
3. Examples / Troubleshooting セクションの有無確認
4. 違反箇所をリストアップし、修正案を提示
Result: 準拠/非準拠の監査レポート

## Troubleshooting

### 新しいスキルがトリガーされない
症状: スキルが自動ロードされない
原因: `description` にトリガーフレーズがない、または曖昧すぎる
対処: ユーザーが実際に言いそうな具体的フレーズを `Use when ...` で追加

### スキルの指示が無視される
症状: スキルがロードされるが、指示に従わない
原因: 指示が長すぎる / 重要な指示がファイル下部に埋もれている / 抽象的すぎる
対処: 重要な指示を上部に配置。`## Critical` ヘッダーを使用。具体的な手順に書き換え

### スキルが不要な場面でもトリガーされる
症状: 無関係なクエリでスキルがロードされる
原因: `description` が広すぎる
対処: `Do NOT use for ...` のような否定トリガーを追加し、スコープを明確化

---

## 憲法：増殖禁止ルール

**本スキルの内容を複数に分割して個別スキルを作成することを禁止する。**
品質基準は統一的でなければならず、分割は基準の矛盾と執行力の低下を招く。
新しいルールを追加する場合は、本スキルの「絶対原則」セクションに追記するのみとする。
