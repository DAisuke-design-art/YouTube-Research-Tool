import os
import pandas as pd
from dotenv import load_dotenv
from core.analyzer import YouTubeAnalyzer

# Load environment variables
load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    print("Error: YOUTUBE_API_KEY not found in .env")
    exit(1)

print("Initializing Analyzer...")
analyzer = YouTubeAnalyzer(api_key)

print("\nTesting get_trend_videos (Category: Science & Technology = 28)...")
try:
    df = analyzer.get_trend_videos(category_id='28', max_results=5)
    
    if df.empty:
        print("No videos found. Check API quota or region.")
    else:
        print(f"Successfully retrieved {len(df)} videos.")
        print(df[['title', 'view_count', 'gk_score']].head())

except Exception as e:
    print(f"Error: {e}")
