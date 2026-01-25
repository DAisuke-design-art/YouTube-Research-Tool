from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

class YouTubeClient:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.logger = logging.getLogger(__name__)

    def search_videos(self, query, max_results=50, published_after=None):
        """
        Search for videos by keyword.
        """
        try:
            search_response = self.youtube.search().list(
                q=query,
                type='video',
                part='id,snippet',
                maxResults=max_results,
                order='viewCount', # Get popular videos first to filter down
                publishedAfter=published_after
            ).execute()
            
            videos = []
            for search_result in search_response.get('items', []):
                videos.append({
                    'video_id': search_result['id']['videoId'],
                    'title': search_result['snippet']['title'],
                    'channel_id': search_result['snippet']['channelId'],
                    'channel_title': search_result['snippet']['channelTitle'],
                    'published_at': search_result['snippet']['publishedAt'],
                    'thumbnail': search_result['snippet']['thumbnails']['high']['url']
                })
            return videos
            
        except HttpError as e:
            self.logger.error(f"An HTTP error %d occurred:\n%s", e.resp.status, e.content)
            return []

    def get_video_details(self, video_ids):
        """
        Get detailed statistics (views, likes, comments) for a list of video IDs.
        Chunks requests in batches of 50.
        """
        if not video_ids:
            return []
            
        stats = {}
        # API allows max 50 IDs per request
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            try:
                response = self.youtube.videos().list(
                    part='statistics,snippet,contentDetails',
                    id=','.join(chunk)
                ).execute()
                
                for item in response.get('items', []):
                    stats[item['id']] = {
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'like_count': int(item['statistics'].get('likeCount', 0)),
                        'comment_count': int(item['statistics'].get('commentCount', 0)),
                        'duration': item['contentDetails'].get('duration'),
                        'tags': item['snippet'].get('tags', [])
                    }
            except HttpError as e:
                self.logger.error(f"Error fetching video details: {e}")
                
        return stats

    def get_channel_details(self, channel_ids):
        """
        Get subscriber counts for a list of channel IDs.
        Chunks requests in batches of 50.
        """
        if not channel_ids:
            return []
            
        channel_stats = {}
        unique_ids = list(set(channel_ids))
        
        for i in range(0, len(unique_ids), 50):
            chunk = unique_ids[i:i+50]
            try:
                response = self.youtube.channels().list(
                    part='statistics',
                    id=','.join(chunk)
                ).execute()
                
                for item in response.get('items', []):
                    # hiddenSubscriberCount might be true
                    sub_count = item['statistics'].get('subscriberCount')
                    channel_stats[item['id']] = {
                        'subscriber_count': int(sub_count) if sub_count else 0,
                        'video_count': int(item['statistics'].get('videoCount', 0))
                    }
            except HttpError as e:
                self.logger.error(f"Error fetching channel details: {e}")
                
        return channel_stats
