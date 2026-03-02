import { NextResponse } from 'next/server';
import { YouTubeService } from '@/lib/youtube';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q');
  const startDate = searchParams.get('startDate');
  const endDate = searchParams.get('endDate');
  const videoType = searchParams.get('videoType') as 'any' | 'normal' | 'shorts' | null;
  const channelId = searchParams.get('channelId');

  if (!q) {
    return NextResponse.json({ error: 'Keyword is required' }, { status: 400 });
  }

  try {
    const results = await YouTubeService.searchPopularDomesticVideos(
      q,
      startDate || undefined,
      endDate || undefined,
      videoType || 'normal',
      channelId || undefined
    );
    return NextResponse.json({ results });
  } catch (error: any) {
    console.error('YouTube API Error:', error.message);
    return NextResponse.json({ error: 'Failed to fetch YouTube data.' }, { status: 500 });
  }
}
