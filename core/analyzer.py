import pandas as pd
from .youtube_client import YouTubeClient
import logging
import isodate
from collections import Counter

class YouTubeAnalyzer:
    def __init__(self, api_key):
        self.client = YouTubeClient(api_key)
        self.logger = logging.getLogger(__name__)

    def find_giant_killing_videos(self, query, max_search_results=50, min_views=10000, max_subs=10000, published_after=None, video_type_filter='long', min_duration=None, max_duration=None):
        """
        Orchestrates the search and analysis flow.
        ...
        5. Filter by video type (Shorts vs Long) OR explicit duration
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
        
        # 4. Merge Data & Filter by Duration
        results = []
        for v in videos:
            vid = v['video_id']
            cid = v['channel_id']
            
            v_stat = video_stats.get(vid, {})
            c_stat = channel_stats.get(cid, {})
            
            # --- Duration Filter ---
            duration_iso = v_stat.get('duration')
            if duration_iso:
                try:
                    duration_seconds = isodate.parse_duration(duration_iso).total_seconds()
                    
                    # Explicit Duration Filter (from Slider) overrides/supplements Type Filter
                    if min_duration is not None and duration_seconds < min_duration:
                        continue
                    if max_duration is not None and duration_seconds > max_duration:
                        continue
                        
                    # Fallback Type Filter (if no explicit slider used, or complementary)
                    # We only apply strict default logic if specific sliders aren't controlling it, 
                    # OR we can treat the "Type" as a preset for the sliders in the UI. 
                    # For now, let's keep the boolean logic for safety if sliders are default.
                    
                    # NOTE: YouTube Shorts can sometimes be slightly over 60s (e.g. 61s). 
                    # We use 65s as a safe threshold for 'auto' detection.
                    is_short = duration_seconds <= 65 
                    
                    if video_type_filter == 'long' and is_short:
                        continue # Skip Shorts
                    elif video_type_filter == 'short' and not is_short:
                        continue # Skip Long videos

                except Exception as e:
                    self.logger.warning(f"Failed to parse duration for {vid}: {e}")
            # -----------------------

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
                'gk_score': round(gk_score, 2),
                'duration_sec': duration_seconds if duration_iso else 0 # For reference
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

    def get_trend_videos(self, category_id=None, max_results=50, region_code='JP', min_duration=None):
        """
        Fetch trending videos using Search API (pseudo-trend) to allow better duration filtering.
        """
        # Determine duration filter for API
        video_duration = None
        if min_duration:
             if min_duration >= 20:
                 video_duration = 'long' # > 20 mins
             elif min_duration >= 4:
                 video_duration = 'medium' # 4-20 mins (Effective "Not Short" filter)
        
        # Determine "Freshness" (e.g., last 30 days for broader trends, or 7 days)
        # To get "Trends", we want reasonably recent high velocity. 
        # But generic search needs a window. Let's say 1 month to catch "Rising" stars.
        import datetime
        from datetime import datetime, timedelta
        one_month_ago = (datetime.now() - timedelta(days=30)).isoformat("T") + "Z"

        # Search Query: use empty string or '*' is risky
        # Usually q=' ' works better combined with category
        query = " "
        
        # FETCH from Search API
        videos = self.client.search_videos(
            query=query,
            max_results=max_results, # Search API allows up to 50 per page. 
            published_after=one_month_ago,
            video_category_id=category_id,
            video_duration=video_duration,
            order='viewCount',
            region_code=region_code,
            relevance_language='ja'
        )
        
        if not videos:
            return pd.DataFrame()
            
        # Enrich with Stats (Views, etc - Search API only gives snippet)
        video_ids = [v['video_id'] for v in videos]
        video_stats = self.client.get_video_details(video_ids)

        channel_ids = [v['channel_id'] for v in videos]
        channel_stats = self.client.get_channel_details(channel_ids)

        results = []
        for v in videos:
            vid = v['video_id']
            cid = v['channel_id']
            
            v_stat = video_stats.get(vid, {})
            c_stat = channel_stats.get(cid, {})
            
            # Parse Duration
            duration_iso = v_stat.get('duration') # Get full duration from details
            duration_seconds = 0
            if duration_iso:
                try:
                    duration_seconds = isodate.parse_duration(duration_iso).total_seconds()
                except:
                    pass
            
            # Filter by Duration (Client-side double check for 'any' case or fine tuning)
            # API 'medium' guarantees 4-20, 'long' > 20.
            # If min_duration is e.g. 5, API 'medium' gives 4+, so we still need check.
            if min_duration is not None and duration_seconds < (min_duration * 60):
                continue

            view_count = v_stat.get('view_count', 0)
            sub_count = c_stat.get('subscriber_count', 0)
            
            # Calculate Giant Killing Score
            gk_score = 0
            if sub_count > 0:
                gk_score = round(view_count / sub_count, 2)
            else:
                gk_score = 0 # Avoid infinity, or treat as massive? 0 is safer.

            results.append({
                'video_id': vid,
                'title': v['title'],
                'channel_id': cid,
                'channel_title': v['channel_title'],
                'published_at': v['published_at'],
                'thumbnail': v['thumbnail'],
                'view_count': view_count,
                'subscriber_count': sub_count,
                'gk_score': gk_score,
                'duration_sec': duration_seconds,
                'tags': v_stat.get('tags', []) # Tags are in video details
            })

        df = pd.DataFrame(results)
        return df
            


    def analyze_tags(self, df):
        """
        Analyze tags from the dataframe and return a frequency dataframe.
        """
        if df.empty or 'tags' not in df.columns:
            return pd.DataFrame()

        all_tags = []
        for tags in df['tags']:
            if isinstance(tags, list):
                all_tags.extend(tags)
            elif isinstance(tags, str):
                # Fallback if somehow tags are strings
                all_tags.append(tags)

        # Count frequencies
        tag_counts = Counter(all_tags)
        
        # Convert to DataFrame
        tag_df = pd.DataFrame(tag_counts.items(), columns=['tag', 'count'])
        tag_df = tag_df.sort_values(by='count', ascending=False).reset_index(drop=True)
        
        return tag_df
