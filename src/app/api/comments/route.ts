import { NextResponse } from 'next/server';
import axios from 'axios';

const API_KEY = process.env.YOUTUBE_API_KEY;
const BASE_URL = 'https://www.googleapis.com/youtube/v3';

export interface CommentData {
    id: string;
    authorDisplayName: string;
    authorChannelId: string;
    textDisplay: string;
    likeCount: number;
    publishedAt: string;
}

export interface CommentThread {
    topLevelComment: CommentData;
    replies: CommentData[];
}

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const videoId = searchParams.get('videoId');

    if (!videoId) {
        return NextResponse.json({ error: 'videoId is required' }, { status: 400 });
    }

    if (!API_KEY) {
        return NextResponse.json({ error: 'YouTube API Key is not set' }, { status: 500 });
    }

    try {
        const allThreads: CommentThread[] = [];
        let nextPageToken: string | undefined = undefined;
        const MAX_PAGES = 20; // 最大2000件

        for (let page = 0; page < MAX_PAGES; page++) {
            const response: any = await axios.get(`${BASE_URL}/commentThreads`, {
                params: {
                    part: 'snippet,replies',
                    videoId,
                    key: API_KEY,
                    maxResults: 100,
                    textFormat: 'plainText',
                    order: 'relevance',
                    ...(nextPageToken ? { pageToken: nextPageToken } : {}),
                },
            });

            const items = response.data.items || [];
            const mappedThreads: CommentThread[] = items.map((item: any) => ({
                topLevelComment: {
                    id: item.id,
                    authorDisplayName: item.snippet.topLevelComment.snippet.authorDisplayName,
                    authorChannelId: item.snippet.topLevelComment.snippet.authorChannelId?.value || '',
                    textDisplay: item.snippet.topLevelComment.snippet.textDisplay,
                    likeCount: item.snippet.topLevelComment.snippet.likeCount,
                    publishedAt: item.snippet.topLevelComment.snippet.publishedAt,
                },
                replies: (item.replies?.comments || []).map((reply: any) => ({
                    id: reply.id,
                    authorDisplayName: reply.snippet.authorDisplayName,
                    authorChannelId: reply.snippet.authorChannelId?.value || '',
                    textDisplay: reply.snippet.textDisplay,
                    likeCount: reply.snippet.likeCount,
                    publishedAt: reply.snippet.publishedAt,
                })),
            }));

            allThreads.push(...mappedThreads);
            nextPageToken = response.data.nextPageToken;
            if (!nextPageToken) break;
        }

        return NextResponse.json({ comments: allThreads });
    } catch (error: any) {
        const message = error.response?.data?.error?.message || error.message || 'Unknown error';
        console.error('Comments API Error:', message);
        return NextResponse.json({ error: `Failed to fetch comments: ${message}` }, { status: 500 });
    }
}
