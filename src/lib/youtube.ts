import axios from 'axios';
import { format } from 'date-fns';
import {
  YouTubeSearchResult,
  YouTubeVideoDetail,
  YouTubeChannelDetail,
  VideoItem
} from '@/types/youtube';
import { filterDomesticVideos } from './filter';

const API_KEY = process.env.YOUTUBE_API_KEY;
const BASE_URL = 'https://www.googleapis.com/youtube/v3';

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
    if (!API_KEY) {
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
        key: API_KEY,
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

      const searchResponse = await axios.get(`${BASE_URL}/search`, {
        params: searchParams
      });

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
          axios.get(`${BASE_URL}/videos`, {
            params: {
              part: 'statistics,contentDetails', // ★ contentDetails を追加（duration取得）
              id: batch.join(','),
              key: API_KEY,
            }
          })
        )
      ),
      Promise.all(
        channelBatches.map(batch =>
          axios.get(`${BASE_URL}/channels`, {
            params: {
              part: 'snippet,statistics',
              id: batch.join(','),
              key: API_KEY,
            }
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
    // フェーズ4: 国内フィルタリング
    // ============================
    const filteredItems = filterDomesticVideos(mappedItems);

    // ============================
    // フェーズ5: 動画タイプに応じたフィルタリング（通常/ショート/すべて）
    // ============================
    const nonShortsItems = filteredItems.filter((item: VideoItem) => {
      if (videoType === 'any') return true;
      if (!item.duration) return true; // duration情報がない場合は判定不能として残す

      const seconds = parseDurationToSeconds(item.duration);
      if (videoType === 'normal') {
        return seconds > 60; // 60秒超の動画のみ残す
      } else if (videoType === 'shorts') {
        return seconds <= 60; // 60秒以下の動画のみ残す
      }
      return true;
    });

    // ============================
    // フェーズ6: 再生数降順ソート
    // ============================
    return nonShortsItems.sort((a: VideoItem, b: VideoItem) => b.viewCount - a.viewCount);
  }
}
