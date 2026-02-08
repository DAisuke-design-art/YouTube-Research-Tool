
from googleapiclient.discovery import build
import os
import json

def analyze_channel(handle):
    api_key = "AIzaSyBXvqYJWWRhZfeaQzQDFFRzQ1uDTdlu2Wo" 
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    print(f"Searching for handle: {handle}")
    
    # 1. Find Channel ID
    search_response = youtube.search().list(
        q=handle,
        type="channel",
        part="id,snippet",
        maxResults=1
    ).execute()
    
    if not search_response.get("items"):
        print("Channel not found.")
        return
        
    channel_id = search_response["items"][0]["id"]["channelId"]
    channel_title = search_response["items"][0]["snippet"]["title"]
    
    # 2. Get Channel Stats
    channel_response = youtube.channels().list(
        id=channel_id,
        part="statistics,contentDetails"
    ).execute()
    
    stats = channel_response["items"][0]["statistics"]
    uploads_playlist = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    subscriber_count = int(stats.get("subscriberCount", 0))
    video_count = int(stats.get("videoCount", 0))
    
    print(f"Channel: {channel_title} ({channel_id})")
    print(f"Subscribers: {subscriber_count}")
    print(f"Total Videos: {video_count}")
    
    # 3. Get Recent Videos
    playlist_response = youtube.playlistItems().list(
        playlistId=uploads_playlist,
        part="snippet",
        maxResults=10
    ).execute()
    
    print("\n--- Recent 10 Videos ---")
    videos = []
    for item in playlist_response["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        
        # Get video stats for views
        vid_stats = youtube.videos().list(
            id=video_id,
            part="statistics,snippet"
        ).execute()
        
        if vid_stats["items"]:
            view_count = int(vid_stats["items"][0]["statistics"].get("viewCount", 0))
            duration = vid_stats["items"][0]["snippet"].get("publishedAt") # actually timestamp
            
            gk_score = 0
            if subscriber_count > 0:
                gk_score = view_count / subscriber_count
                
            print(f"Title: {title}")
            print(f"Views: {view_count:,} | GK Score: {gk_score:.2f}")
            videos.append({"title": title, "views": view_count, "gk": gk_score})

analyze_channel("@tokiwokakeru.zundamon")
