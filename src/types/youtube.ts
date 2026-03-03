export interface VideoItem {
  videoId: string;
  channelId: string;
  title: string;
  channelTitle: string;
  publishedAt: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  subscriberCount: number;
  videoUrl: string;
  thumbnailUrl: string;
  researchDate: string;
  channelCountry?: string; // Debugging
  duration?: string; // ISO 8601 形式 (例: "PT1M30S")。ショート動画判定に使用
  isShort?: boolean; // YouTube Shorts判定結果（複合ロジックで判定）
  // 算出指標
  likeRate: number;       // 高評価率 = likeCount / viewCount
  commentRate: number;    // コメント率 = commentCount / viewCount
  viewSubRatio: number;   // View/Sub比 = viewCount / subscriberCount
  dailyAvgViews: number;  // 日次平均再生 = viewCount / 経過日数
}

// API Responses typing
export interface YouTubeSearchResult {
  id: {
    videoId: string;
  };
  snippet: {
    title: string;
    channelId: string;
    channelTitle: string;
    publishedAt: string;
    description: string;
    thumbnails: {
      high?: {
        url: string;
      };
      medium?: {
        url: string;
      };
    };
  };
}

export interface YouTubeVideoDetail {
  id: string;
  statistics: {
    viewCount?: string;
    likeCount?: string;
    commentCount?: string;
  };
  contentDetails?: {
    duration?: string; // ISO 8601 形式 (例: "PT1M30S")
  };
}

export interface YouTubeChannelDetail {
  id: string;
  snippet: {
    country?: string;
  };
  statistics: {
    subscriberCount?: string;
  };
}

