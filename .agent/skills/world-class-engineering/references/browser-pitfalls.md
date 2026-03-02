# Browser Pitfalls — ブラウザ固有の既知問題パターン集

> ブラウザのAPI/挙動において、仕様と実装が乖離しているケース、
> またはブラウザ間で挙動が異なるケースを蓄積する。

---

## Pitfall #001: Blob URL + download属性によるファイルダウンロード

### 標準的な実装パターン

```javascript
const blob = new Blob([data], { type: 'text/csv' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'filename.csv';
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
```

### 既知の問題

| # | 問題 | 影響ブラウザ | 原因 | 回避策 |
|---|---|---|---|---|
| 1 | ファイル名がUUID（blob:のハッシュ）になる | Chrome, Safari (一部バージョン) | `revokeObjectURL` の呼び出しが早すぎ、ダウンロードマネージャがファイル名メタデータを読み取る前にBlobがGCされる | `revokeObjectURL` を遅延させる（数秒後）、または呼ばない |
| 2 | ファイル名からマルチバイト文字が消える | Chrome (macOS) | `download` 属性のファイル名にマルチバイト文字（日本語等）が含まれる場合、Content-Disposition相当の処理でエンコードに失敗する | ファイル名をASCII文字のみで構成する |
| 3 | Base64 Data URIでダウンロードが発動しない | Safari | Safariは `data:` URIスキームの `download` 属性を無視する仕様 | Blob URL方式を使用する |
| 4 | 巨大なBase64 Data URIでメモリ不足 | 全ブラウザ | 数MB以上のファイルをBase64に変換するとURL文字列が巨大になり、メモリを圧迫する | Blob URL方式を使用する |
| 5 | `a.click()` がDOMに追加される前に発火 | Firefox (一部バージョン) | `appendChild` 後に即座に `click()` すると、DOMツリーへの反映が完了していない場合がある | `setTimeout` または `requestAnimationFrame` で1フレーム待機してから `click()` を実行する |

### 診断チェックリスト

ファイルダウンロード機能で問題が発生した場合、以下の順序で診断する：

1. ブラウザのDevTools → Network タブを開き、ダウンロードリクエストの Content-Disposition ヘッダーを確認
2. Console タブで JavaScript エラーが出ていないか確認
3. `a.download` 属性の値をコンソールで出力し、ファイル名が正しく設定されているか確認
4. `URL.createObjectURL` の戻り値が `blob:` で始まる有効なURLか確認
5. ユーザーのブラウザ名・バージョン・OS を確認

### 最も安全な実装パターン（推奨）

```javascript
// 1. ファイル名はASCII文字のみで構成する
const filename = `YoutubeResearch_${timestamp}.csv`;

// 2. Blob URLを生成
const blob = new Blob([data], { type: 'application/octet-stream' });
const url = URL.createObjectURL(blob);

// 3. aタグを生成しDOMに追加
const a = document.createElement('a');
a.style.display = 'none';
a.href = url;
a.download = filename;
document.body.appendChild(a);

// 4. 1フレーム待機してからクリック
setTimeout(() => {
    a.click();
    // 5. クリーンアップ（revokeは呼ばない。GCに任せる）
    setTimeout(() => document.body.removeChild(a), 200);
}, 0);
```

> **注意**: この「推奨パターン」でも問題が解決しない場合、原因はクライアントサイドのJavaScriptではなく、ブラウザの設定（ダウンロード先の設定、セキュリティ拡張機能等）にある可能性が高い。その場合はサーバーサイドでファイルを生成し、通常のHTTPレスポンスとしてダウンロードさせるアプローチに切り替えること。

---

## Pitfall #002: Content-Type と download 属性の相互作用

### 既知の問題

| MIME Type | download属性の挙動 |
|---|---|
| `application/octet-stream` | ✅ ほぼ全ブラウザで `download` 属性が尊重される |
| `text/csv` | ⚠️ 一部ブラウザがインラインで開こうとする |
| `text/plain` | ⚠️ ブラウザがファイルを直接表示する（ダウンロードではなく） |
| `application/vnd.openxmlformats-...` | ⚠️ Chromeが独自のダウンロードハンドラを使用し、`download` 属性のファイル名を無視することがある |

### 推奨

ダウンロードを確実に発動させたい場合、MIME Typeは **`application/octet-stream`** を使用する。
これはブラウザに「このデータはバイナリであり、表示ではなくダウンロードすべき」と強制するシグナルとなる。
