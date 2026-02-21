import os
from googleapiclient.discovery import build
import json

api_key = os.environ.get("YOUTUBE_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("YOUTUBE_API_KEY")

youtube = build('youtube', 'v3', developerKey=api_key)

request = youtube.search().list(
    part="snippet",
    q="n8n Youtube",
    type="video",
    maxResults=50,
    order="viewCount",
    regionCode="JP",
    relevanceLanguage="ja"
)
response = request.execute()

results = []
for item in response.get("items", []):
    results.append({
        "title": item["snippet"]["title"],
        "channelTitle": item["snippet"]["channelTitle"],
        "videoId": item["id"]["videoId"]
    })

print(json.dumps(results, indent=2, ensure_ascii=False))
