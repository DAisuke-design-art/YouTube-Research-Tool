import os
from googleapiclient.discovery import build
import json
import isodate

api_key = os.environ.get("YOUTUBE_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("YOUTUBE_API_KEY")

youtube = build('youtube', 'v3', developerKey=api_key)

# Check specifically for the video lq7jL02rOsg
video_id = "lq7jL02rOsg"
print(f"Checking data for {video_id}...")

request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    id=video_id
)
response = request.execute()

for item in response.get("items", []):
    print(f"Title: {item['snippet']['title']}")
    print(f"Channel: {item['snippet']['channelTitle']}")
    print(f"Published: {item['snippet']['publishedAt']}")
    print(f"Views: {item['statistics'].get('viewCount')}")
    print(f"Tags: {item['snippet'].get('tags', [])}")
    duration = isodate.parse_duration(item['contentDetails'].get('duration', 'PT0S')).total_seconds()
    print(f"Duration (sec): {duration}")

