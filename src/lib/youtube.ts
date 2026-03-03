import axios from 'axios';
import { format } from 'date-fns';
import {
  YouTubeSearchResult,
  YouTubeVideoDetail,
  YouTubeChannelDetail,
  VideoItem
} from '@/types/youtube';
import { filterDomesticVideos } from './filter';

const BASE_URL = 'https://www.googleapis.com/youtube/v3';

/**
 * 環境変数から全てのYouTube APIキーを収集する
 * YOUTUBE_API_KEY, YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, ... を自動検出
 */
function collectApiKeys(): string[] {
  const keys: string[] = [];

  // メインキー
  if (process.env.YOUTUBE_API_KEY) {
    keys.push(process.env.YOUTUBE_API_KEY);
  }

  // 番号付きキーを走査（1〜10）
  for (let i = 1; i <= 10; i++) {
    const key = process.env[`YOUTUBE_API_KEY_${i}`];
    if (key && !key.includes('のキー')) { // プレースホルダーを除外
      keys.push(key);
    }
  }

  return keys;
}

const API_KEYS = collectApiKeys();
let currentKeyIndex = 0;

function getCurrentApiKey(): string {
  if (API_KEYS.length === 0) {
    throw new Error('YouTube API Key is not set');
  }
  return API_KEYS[currentKeyIndex];
}

/**
 * APIキーフォールバック付きのaxios GETリクエスト
 * 403（クォータ超過）発生時に次のキーへ自動切り替え
 */
async function apiGet(url: string, params: Record<string, any>): Promise<any> {
  let lastError: any = null;
  const triedKeys = new Set<number>();

  while (triedKeys.size < API_KEYS.length) {
    triedKeys.add(currentKeyIndex);
    const apiKey = getCurrentApiKey();

    try {
      const response = await axios.get(url, {
        params: { ...params, key: apiKey },
      });
      return response;
    } catch (error: any) {
      const status = error?.response?.status;
      const reason = error?.response?.data?.error?.errors?.[0]?.reason;

      // クォータ超過 or 認証エラー → 次のキーへフォールバック
      if (status === 403 || status === 429) {
        console.warn(
          `⚠️ APIキー #${currentKeyIndex + 1} がクォータ超過 (${reason || status}). 次のキーへ切り替え...`
        );
        lastError = error;
        currentKeyIndex = (currentKeyIndex + 1) % API_KEYS.length;
        continue;
      }

      // それ以外のエラーはそのままスロー
      throw error;
    }
  }

  // 全キー枯渇
  console.error('🚨 全てのAPIキーがクォータ超過しています');
  throw lastError || new Error('All YouTube API keys have exceeded their quota.');
}

/**
 * ISO 8601 duration (例: "PT1M30S") を秒数に変換する
 */
function parseDurationToSeconds(duration: string): number {
  const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return 0;
  const hours = parseInt(match[1] || '0', 10);
  const minutes = parseInt(match[2] || '0', 10);
  const seconds = parseInt(match[3] || '0', 10);
  return hours * 3600 + minutes * 60 + seconds;
}

export class YouTubeService {
  /**
   * 検索実行のメインエントリーポイント
   * 
   * 方式δ（承認済み大域解）:
   * 1. relevanceLanguage=ja で日本語動画を優先
   * 2. nextPageToken を使って複数ページ取得（母数拡大）
   * 3. contentDetails で duration を取得し、ショート動画（≤60秒）を除外
   */
  static async searchPopularDomesticVideos(
    query: string,
    startDate?: string,
    endDate?: string,
    videoType: 'any' | 'normal' | 'shorts' = 'normal',
    channelId?: string
  ): Promise<VideoItem[]> {
    if (API_KEYS.length === 0) {
      throw new Error('YouTube API Key is not set');
    }

    // ============================
    // フェーズ1: 複数ページの検索ID取得
    // ============================
    const MAX_PAGES = 3; // 最大3ページ（150件）
    let allSearchItems: YouTubeSearchResult[] = [];
    let nextPageToken: string | undefined = undefined;

    for (let page = 0; page < MAX_PAGES; page++) {
      const searchParams: any = {
        part: 'snippet',
        q: query,
        type: 'video',
        regionCode: 'JP',
        relevanceLanguage: 'ja', // ★ 日本語動画の関連度を優先
        order: 'relevance',
        maxResults: 50,
        ...(channelId ? { channelId } : {}),
      };

      if (startDate) {
        searchParams.publishedAfter = `${startDate}T00:00:00Z`;
      }
      if (endDate) {
        searchParams.publishedBefore = `${endDate}T23:59:59Z`;
      }
      if (nextPageToken) {
        searchParams.pageToken = nextPageToken;
      }

      const searchResponse = await apiGet(`${BASE_URL}/search`, searchParams);

      const items: YouTubeSearchResult[] = searchResponse.data.items || [];
      allSearchItems = allSearchItems.concat(items);

      // 次のページトークンがなければ終了
      nextPageToken = searchResponse.data.nextPageToken;
      if (!nextPageToken) break;
    }

    if (allSearchItems.length === 0) {
      return [];
    }

    // 重複除去（複数ページで同一動画が返される可能性への対策）
    const uniqueItems = allSearchItems.filter((item, index, self) =>
      index === self.findIndex(t => t.id.videoId === item.id.videoId)
    );

    // ============================
    // フェーズ2: メタデータ一括取得（Bulk Item Fetch）
    // ============================
    // videos.list は最大50件ずつなので、50件ごとにバッチ処理
    const videoIds = uniqueItems.map(item => item.id.videoId);
    const channelIds = [...new Set(uniqueItems.map(item => item.snippet.channelId))];

    // videos.list をバッチ化（50件ずつ）
    const videoBatches: string[][] = [];
    for (let i = 0; i < videoIds.length; i += 50) {
      videoBatches.push(videoIds.slice(i, i + 50));
    }

    const channelBatches: string[][] = [];
    for (let i = 0; i < channelIds.length; i += 50) {
      channelBatches.push(channelIds.slice(i, i + 50));
    }

    // 全バッチを並列実行
    const [videoResults, channelResults] = await Promise.all([
      Promise.all(
        videoBatches.map(batch =>
          apiGet(`${BASE_URL}/videos`, {
            part: 'statistics,contentDetails', // ★ contentDetails を追加（duration取得）
            id: batch.join(','),
          })
        )
      ),
      Promise.all(
        channelBatches.map(batch =>
          apiGet(`${BASE_URL}/channels`, {
            part: 'snippet,statistics',
            id: batch.join(','),
          })
        )
      ),
    ]);

    // レスポンスを結合してMapに変換
    const videosData: Record<string, YouTubeVideoDetail> = {};
    videoResults.forEach(response => {
      response.data.items.forEach((item: YouTubeVideoDetail) => {
        videosData[item.id] = item;
      });
    });

    const channelsData: Record<string, YouTubeChannelDetail> = {};
    channelResults.forEach(response => {
      response.data.items.forEach((item: YouTubeChannelDetail) => {
        channelsData[item.id] = item;
      });
    });

    // ============================
    // フェーズ3: 構造体マッピング
    // ============================
    const currentResearchDate = format(new Date(), 'yyyy/MM/dd HH:mm:ss');
    const mappedItems: (VideoItem & { _rawDescription: string })[] = uniqueItems.map(item => {
      const videoDetail = videosData[item.id.videoId];
      const videoStat = videoDetail?.statistics || {};
      const channelData = channelsData[item.snippet.channelId];
      const duration = videoDetail?.contentDetails?.duration || '';

      const viewCount = parseInt(videoStat.viewCount || '0', 10);
      const likeCount = parseInt(videoStat.likeCount || '0', 10);
      const commentCount = parseInt(videoStat.commentCount || '0', 10);
      const subscriberCount = parseInt(channelData?.statistics?.subscriberCount || '0', 10);

      // 算出指標
      const publishedDate = new Date(item.snippet.publishedAt);
      const daysSincePublished = Math.max(1, Math.floor((Date.now() - publishedDate.getTime()) / (1000 * 60 * 60 * 24)));
      const likeRate = viewCount > 0 ? likeCount / viewCount : 0;
      const commentRate = viewCount > 0 ? commentCount / viewCount : 0;
      const viewSubRatio = subscriberCount > 0 ? viewCount / subscriberCount : 0;
      const dailyAvgViews = viewCount / daysSincePublished;

      return {
        videoId: item.id.videoId,
        channelId: item.snippet.channelId,
        title: item.snippet.title,
        channelTitle: item.snippet.channelTitle,
        publishedAt: format(publishedDate, 'yyyy/MM/dd'),
        viewCount,
        likeCount,
        commentCount,
        subscriberCount,
        videoUrl: `https://www.youtube.com/watch?v=${item.id.videoId}`,
        // mqdefault.jpg (medium) は 320x180 の16:9比率で上下の黒帯が入らない
        thumbnailUrl: item.snippet.thumbnails?.medium?.url || item.snippet.thumbnails?.high?.url || '',
        researchDate: currentResearchDate,
        channelCountry: channelData?.snippet?.country,
        duration: duration,
        likeRate,
        commentRate,
        viewSubRatio,
        dailyAvgViews,
        _rawDescription: item.snippet.description,
      };
    });

    // ============================
    // フェーズ4: Shorts判定（API情報のみ — 複合ロジック）
    // ============================
    // ※ _rawDescription が利用可能なこの段階で判定する
    // （フェーズ5の国内フィルタで _rawDescription が削除されるため）
    mappedItems.forEach(item => {
      item.isShort = isShortByApiData(
        item.duration || '',
        item.title,
        (item as any)._rawDescription || ''
      );
    });

    // ============================
    // フェーズ5: 国内フィルタリング
    // ============================
    const filteredItems = filterDomesticVideos(mappedItems);

    // ============================
    // フェーズ6: 動画タイプに応じたフィルタリング
    // ============================
    const typeFilteredItems = filteredItems.filter((item: VideoItem) => {
      if (videoType === 'any') return true;
      if (videoType === 'normal') return !item.isShort;
      if (videoType === 'shorts') return item.isShort === true;
      return true;
    });

    // ============================
    // フェーズ7: 再生数降順ソート
    // ============================
    return typeFilteredItems.sort((a: VideoItem, b: VideoItem) => b.viewCount - a.viewCount);
  }
}

// ============================
// Shorts判定ヘルパー（API情報のみ — 複合ロジック）
// ============================

/**
 * YouTube Data API v3 の情報のみでShorts判定。
 *
 * - > 180秒    → 通常動画（確定: Shorts上限は3分）
 * - ≤ 60秒     → Shorts（確定: ほぼ全てのShortsはこの範囲）
 * - 61〜180秒  → タイトル/説明文に #shorts タグがあればShorts
 * - 61〜180秒 + タグなし → 通常動画（安全側: 誤除外を防ぐ）
 */
function isShortByApiData(
  duration: string,
  title: string,
  description: string
): boolean {
  const seconds = parseDurationToSeconds(duration);
  if (seconds === 0) return false;      // duration不明 → 安全側（通常動画扱い）
  if (seconds > 180) return false;      // 180秒超 → 確実に非Shorts
  if (seconds <= 60) return true;       // 60秒以下 → ほぼ確実にShorts
  // 61〜180秒: タイトル/説明文に #shorts タグがあればShorts
  const text = (title + ' ' + description).toLowerCase();
  return /#shorts?\b/.test(text);
}
