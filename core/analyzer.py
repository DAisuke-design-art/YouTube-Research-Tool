import pandas as pd
from .youtube_client import YouTubeClient
import logging

class YouTubeAnalyzer:
    def __init__(self, api_key):
        self.client = YouTubeClient(api_key)
        self.logger = logging.getLogger(__name__)

    def find_giant_killing_videos(self, query, max_search_results=50, min_views=10000, max_subs=10000, published_after=None):
        """
        Orchestrates the search and analysis flow.
        1. Search videos
        2. Get video stats (Views)
        3. Get channel stats (Subs)
        4. Calculate metrics and filter
        """
        # 1. Search
        videos = self.client.search_videos(query, max_results=max_search_results, published_after=published_after)
        if not videos:
            return pd.DataFrame()
        
        video_ids = [v['video_id'] for v in videos]
        channel_ids = [v['channel_id'] for v in videos]
        
        # 2. Get Video Stats (Views, etc)
        video_stats = self.client.get_video_details(video_ids)
        
        # 3. Get Channel Stats (Subs)
        channel_stats = self.client.get_channel_details(channel_ids)
        
        # 4. Merge Data
        results = []
        for v in videos:
            vid = v['video_id']
            cid = v['channel_id']
            
            v_stat = video_stats.get(vid, {})
            c_stat = channel_stats.get(cid, {})
            
            view_count = v_stat.get('view_count', 0)
            sub_count = c_stat.get('subscriber_count', 0)
            
            # Basic Filtering strictly based on arguments
            # Note: sub_count 0 means hidden or error, we might want to include or exclude
            # Here we act permissive if sub_count is 0 but show it. 
            # But the requirement is "Subs < 10k". 
            
            gk_score = 0
            if sub_count > 0:
                gk_score = view_count / sub_count
            elif sub_count == 0 and view_count > 0:
                gk_score = 999 # Infinitely good if 0 subs? Or hidden. Treat as high.
            
            data = {
                'title': v['title'],
                'video_id': vid,
                'channel_title': v['channel_title'],
                'channel_id': cid,
                'published_at': v['published_at'],
                'thumbnail': v['thumbnail'],
                'view_count': view_count,
                'like_count': v_stat.get('like_count', 0),
                'comment_count': v_stat.get('comment_count', 0),
                'subscriber_count': sub_count,
                'video_count': c_stat.get('video_count', 0),
                'tags': v_stat.get('tags', []),
                'gk_score': round(gk_score, 2)
            }
            results.append(data)
            
        df = pd.DataFrame(results)
        
        if df.empty:
            return df
            
        # Filter Logic
        # Condition 1: Views >= min_views
        # Condition 2: Subs <= max_subs
        
        filtered_df = df[
            (df['view_count'] >= min_views) & 
            (df['subscriber_count'] <= max_subs)
        ].copy()
        
        # Sort by GK Score descending
        filtered_df = filtered_df.sort_values(by='gk_score', ascending=False)
        
        return filtered_df
