import { NextRequest, NextResponse } from 'next/server';
import ExcelJS from 'exceljs';

interface ExportRequestBody {
  data: Array<{
    researchDate: string;
    title: string;
    channelTitle: string;
    publishedAt: string;
    subscriberCount: number;
    viewCount: number;
    likeCount: number;
    commentCount: number;
    videoUrl: string;
    thumbnailUrl: string;
    likeRate: number;
    commentRate: number;
    viewSubRatio: number;
    dailyAvgViews: number;
  }>;
  keyword: string;
  comments?: Record<string, Array<{
    topLevelComment: {
      id: string;
      authorDisplayName: string;
      textDisplay: string;
      likeCount: number;
      publishedAt: string;
    };
    replies: Array<{
      id: string;
      authorDisplayName: string;
      textDisplay: string;
      likeCount: number;
      publishedAt: string;
    }>;
  }>>;
}

/**
 * ASCII文字のみの安全なタイムスタンプ文字列を生成
 */
function getTimestamp(): string {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
}

/**
 * XLSX出力: ExcelJS を使用し、サムネイル画像埋め込み＋動画URLハイパーリンク付き
 */
async function generateXlsx(data: ExportRequestBody['data'], keyword: string, comments?: ExportRequestBody['comments']): Promise<Buffer> {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('ResearchData');

  // カラム定義
  worksheet.columns = [
    { header: '調査日時', key: 'researchDate', width: 22 },
    { header: '検索キーワード', key: 'keyword', width: 16 },
    { header: 'タイトル', key: 'title', width: 40 },
    { header: '公開日', key: 'publishedAt', width: 12 },
    { header: '登録者数', key: 'subscriberCount', width: 12 },
    { header: '再生数', key: 'viewCount', width: 12 },
    { header: 'いいね数', key: 'likeCount', width: 10 },
    { header: 'コメント数', key: 'commentCount', width: 10 },
    { header: '高評価率', key: 'likeRate', width: 12 },
    { header: 'コメント率', key: 'commentRate', width: 12 },
    { header: 'View/Sub比', key: 'viewSubRatio', width: 12 },
    { header: '日次平均再生', key: 'dailyAvgViews', width: 14 },
    { header: 'チャンネル名', key: 'channelTitle', width: 20 },
    { header: '動画URL', key: 'videoUrl', width: 40 },
    { header: 'サムネイル', key: 'thumbnail', width: 22 },
  ];

  // 全列のデフォルトアライメント（上下中央、左右中央、折り返し）
  worksheet.columns.forEach((col) => {
    col.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
  });

  // テキストが長くなる列は左揃えにする（読みやすさ重視）
  ['title', 'channelTitle', 'videoUrl'].forEach((key) => {
    worksheet.getColumn(key).alignment = { vertical: 'middle', horizontal: 'left', wrapText: true };
  });

  // ヘッダー行のスタイル
  worksheet.getRow(1).font = { bold: true };
  worksheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' };

  // データ行を追加
  data.forEach((item) => {
    const row = worksheet.addRow({
      researchDate: item.researchDate,
      keyword: keyword,
      title: item.title,
      publishedAt: item.publishedAt,
      subscriberCount: item.subscriberCount,
      viewCount: item.viewCount,
      likeCount: item.likeCount,
      commentCount: item.commentCount,
      likeRate: `${(item.likeRate * 100).toFixed(2)}%`,
      commentRate: `${(item.commentRate * 100).toFixed(3)}%`,
      viewSubRatio: item.viewSubRatio.toFixed(2),
      dailyAvgViews: Math.round(item.dailyAvgViews),
      channelTitle: item.channelTitle,
      videoUrl: '', // ハイパーリンクを後で設定
      thumbnail: '', // 画像埋め込み用
    });

    // 動画URL列にハイパーリンクを設定（クリック可能な青い下線付きリンク）
    const urlCell = row.getCell('videoUrl');
    urlCell.value = {
      text: item.videoUrl,
      hyperlink: item.videoUrl,
    };
    urlCell.font = {
      color: { argb: 'FF1155CC' },
      underline: true,
    };
  });

  // サムネイル画像を並列ダウンロードして埋め込む
  // mqdefault.jpg は 320x180 (16:9)。Excel上でも16:9を維持する
  const THUMBNAIL_WIDTH = 160;
  const THUMBNAIL_HEIGHT = 90;
  const ROW_HEIGHT = 68; // Excelの行の高さ。90px ≈ 67.5pt なので微調整

  const imagePromises = data.map(async (item, index) => {
    try {
      const response = await fetch(item.thumbnailUrl);
      if (!response.ok) return null;
      const arrayBuffer = await response.arrayBuffer();
      return { index, buffer: Buffer.from(arrayBuffer) };
    } catch {
      return null;
    }
  });

  const imageResults = await Promise.all(imagePromises);

  for (const result of imageResults) {
    if (!result) continue;

    const { index, buffer } = result;
    const rowIndex = index + 1;

    worksheet.getRow(rowIndex + 1).height = ROW_HEIGHT;

    const imageId = workbook.addImage({
      buffer: buffer as any,
      extension: 'jpeg',
    });

    worksheet.addImage(imageId, {
      tl: { col: 14, row: rowIndex } as any,
      ext: { width: THUMBNAIL_WIDTH, height: THUMBNAIL_HEIGHT },
    });
  }

  // ============================
  // コメントシート（抽出済みのもののみ）
  // ============================
  if (comments && Object.keys(comments).length > 0) {
    try {
      const commentSheet = workbook.addWorksheet('Comments');

      commentSheet.columns = [
        { header: '動画ID', key: 'videoId', width: 14 },
        { header: '動画タイトル', key: 'videoTitle', width: 30 },
        { header: 'タイプ', key: 'type', width: 8 },
        { header: '親コメントID', key: 'parentId', width: 18 },
        { header: '投稿者', key: 'author', width: 18 },
        { header: '投稿日', key: 'publishedAt', width: 14 },
        { header: 'いいね数', key: 'likeCount', width: 10 },
        { header: 'コメント本文', key: 'text', width: 60 },
        { header: '動画URL', key: 'videoUrl', width: 40 },
      ];

      commentSheet.getRow(1).font = { bold: true };
      commentSheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' };
      commentSheet.getColumn('text').alignment = { vertical: 'middle', horizontal: 'left', wrapText: true };
      commentSheet.getColumn('author').alignment = { vertical: 'middle', horizontal: 'left' };

      // videoIdからタイトルを引くマップ
      const titleMap: Record<string, string> = {};
      data.forEach(item => { titleMap[item.videoUrl.split('v=')[1]] = item.title; });

      let rowCount = 0;
      for (const [videoId, threads] of Object.entries(comments)) {
        const videoTitle = titleMap[videoId] || '';
        const videoUrl = `https://www.youtube.com/watch?v=${videoId}`;

        for (const thread of threads) {
          // 親コメント
          commentSheet.addRow({
            videoId,
            videoTitle,
            type: 'Thread',
            parentId: '',
            author: thread.topLevelComment.authorDisplayName,
            publishedAt: new Date(thread.topLevelComment.publishedAt).toLocaleDateString('ja-JP'),
            likeCount: thread.topLevelComment.likeCount,
            text: thread.topLevelComment.textDisplay,
            videoUrl,
          });
          rowCount++;

          // 返信
          for (const reply of thread.replies) {
            commentSheet.addRow({
              videoId,
              videoTitle,
              type: 'Reply',
              parentId: thread.topLevelComment.id,
              author: reply.authorDisplayName,
              publishedAt: new Date(reply.publishedAt).toLocaleDateString('ja-JP'),
              likeCount: reply.likeCount,
              text: reply.textDisplay,
              videoUrl,
            });
            rowCount++;
          }
        }
      }

    } catch (err: any) {
      console.error('[EXPORT COMMENTS] ERROR generating comment sheet:', err.message, err.stack);
    }
  }

  const excelBuffer = await workbook.xlsx.writeBuffer();
  return Buffer.from(excelBuffer);
}

/**
 * サーバーサイドでExcelファイルを生成し、Content-Dispositionヘッダー付きのHTTPレスポンスとして返す。
 */
export async function POST(request: NextRequest) {
  try {
    const body: ExportRequestBody = await request.json();
    const { data, keyword, comments } = body;



    if (!data || data.length === 0) {
      return NextResponse.json({ error: 'データがありません' }, { status: 400 });
    }

    const timestamp = getTimestamp();
    const buffer = await generateXlsx(data, keyword, comments);
    const filename = `YoutubeResearch_${timestamp}.xlsx`;

    const responseBody = new Uint8Array(buffer);
    return new NextResponse(responseBody, {
      status: 200,
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Content-Length': buffer.length.toString(),
      },
    });
  } catch (error: any) {
    console.error('Export error:', error);
    return NextResponse.json({ error: 'エクスポート中にエラーが発生しました' }, { status: 500 });
  }
}
