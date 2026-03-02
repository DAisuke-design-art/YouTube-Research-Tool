import { VideoItem } from '@/types/youtube';

/**
 * サーバーサイドAPIにデータを送信し、生成されたExcelファイルをダウンロードする。
 * 
 * 設計根拠（world-class-engineering Skill Phase 2 の結論）:
 * クライアントサイドの Blob URL + a.download 方式は、ブラウザ環境依存でファイル名がUUID化する
 * 既知の不具合がある（failure-log.md Entry #001 参照）。
 * サーバーサイドで Content-Disposition ヘッダーを設定する方式は HTTP標準仕様であり、
 * あらゆるブラウザで確実にファイル名と拡張子が付与される。
 */
export const exportData = async (data: VideoItem[], format: 'xlsx', keyword: string, comments?: Record<string, any[]>) => {
  if (!data || data.length === 0) return;

  try {
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data, keyword, comments }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Export failed:', errorData.error);
      alert('エクスポートに失敗しました: ' + errorData.error);
      return;
    }

    const blob = await response.blob();

    // Content-Dispositionヘッダーからファイル名を抽出
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'YoutubeResearch.xlsx';

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    // ブラウザのネイティブダウンロードハンドラを使用
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);

    setTimeout(() => {
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 200);
    }, 0);

  } catch (error: any) {
    console.error('Export error:', error);
    alert('エクスポート中にエラーが発生しました');
  }
};
