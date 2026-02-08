import argparse
import pandas as pd
import json
import os
import sys
import time
from dotenv import load_dotenv
from core.analyzer import YouTubeAnalyzer
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

STATE_FILE = "state.json"
SEEDS_FILE = "seeds.json"

def get_year_ago_iso():
    today = datetime.now()
    return (today - timedelta(days=365)).isoformat("T") + "Z"

def load_api_keys():
    """Loads all YOUTUBE_API_KEY* from env variables."""
    keys = []
    # Check default
    if os.getenv("YOUTUBE_API_KEY"):
        keys.append(os.getenv("YOUTUBE_API_KEY"))
    
    # Check numbered keys
    i = 1
    while True:
        k = os.getenv(f"YOUTUBE_API_KEY_{i}")
        if k:
            keys.append(k)
            i += 1
        else:
            break
    return keys

def get_analyzer(keys):
    """
    Returns an analyzer instance. 
    In a real full implementation, this would handle rotation logic upon usage.
    For this batch script, we try to instantiate with a valid key.
    Current simple logic: use the first available, or allow rotation logic inside the search loop if we wanted complexity.
    For now, let's keep it simple: We pick a key. If it fails during critical call, we could retry.
    """
    if not keys:
         raise Exception("No API Keys found in .env")
    return YouTubeAnalyzer(keys[0]), keys # Return current and list

def load_json_file(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description='Agent Manager CLI')
    parser.add_argument('--mode', type=str, choices=['single', 'batch'], default='single', help='Execution mode')
    parser.add_argument('--keyword', type=str, help='Keyword for single mode')
    parser.add_argument('--limit', type=int, default=3, help='Number of keywords to process in batch mode / Output limit in single mode')
    parser.add_argument('--min_views', type=int, default=3000, help='Minimum views')
    
    args = parser.parse_args()
    
    keys = load_api_keys()
    if not keys:
        print(json.dumps({"error": "No API keys found. Please set YOUTUBE_API_KEY in .env"}))
        sys.exit(1)

    # --- SINGLE MODE (Legacy/Direct) ---
    if args.mode == 'single':
        if not args.keyword:
            print(json.dumps({"error": "--keyword is required for single mode"}))
            sys.exit(1)
            
        try:
            # Simple single key usage for now
            analyzer = YouTubeAnalyzer(keys[0])
            run_single_search(analyzer, args.keyword, args.limit, args.min_views)
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)

    # --- BATCH MANAGER MODE ---
    elif args.mode == 'batch':
        seeds = load_json_file(SEEDS_FILE)
        state = load_json_file(STATE_FILE)
        
        if not seeds:
            print(json.dumps({"error": "seeds.json not found or empty"}))
            sys.exit(1)
        if state is None:
            state = {"current_index": 0}

        start_idx = state.get("current_index", 0)
        # Wrap around if finished
        if start_idx >= len(seeds):
            start_idx = 0
            
        # Determine batch
        batch_size = args.limit # Using limit arg as batch size
        end_idx = min(start_idx + batch_size, len(seeds))
        current_batch = seeds[start_idx:end_idx]
        
        # If batch is smaller than requested because we hit end, wrap around immediately?
        # For simplicity, let's just process what's left. Next run starts at 0.
        
        # Setup Analyzer with Rotation Capability
        current_key_idx = 0
        analyzer = YouTubeAnalyzer(keys[current_key_idx])
        
        results = {} # {keyword: [video_data...]}
        
        processed_count = 0
        
        for kw in current_batch:
            try:
                # Search logic with retry/rotation
                df = None
                attempt = 0
                max_attempts = len(keys)
                
                while attempt < max_attempts:
                    try:
                        df = analyzer.find_giant_killing_videos(
                            kw, 
                            max_search_results=20, # keeping it lighter than 50 for batch speed
                            min_views=args.min_views,
                            max_subs=50000,
                            published_after=get_year_ago_iso(),
                            video_type_filter="long",
                            min_duration=300
                        )
                        break # Success
                    except HttpError as e:
                        if e.resp.status in [403, 429]: # Quota/Rate Limit
                            attempt += 1
                            if attempt < max_attempts:
                                current_key_idx = (current_key_idx + 1) % len(keys)
                                analyzer = YouTubeAnalyzer(keys[current_key_idx])
                                continue
                        raise e # Other error or no keys left

                if df is not None and not df.empty:
                    if 'gk_score' in df.columns:
                        df = df.sort_values(by='gk_score', ascending=False)
                    
                    top = df.head(1).to_dict(orient='records') # Just top 1 per keyword for brevity in batch
                    
                    # Clean up
                    clean_top = []
                    for item in top:
                        clean_item = {
                            k: item[k] for k in ['title', 'gk_score', 'view_count', 'subscriber_count', 'video_id', 'channel_title', 'tags'] if k in item
                        }
                        clean_item['url'] = f"https://www.youtube.com/watch?v={item['video_id']}"
                        clean_top.append(clean_item)
                        
                    results[kw] = clean_top
                else:
                    results[kw] = []
                    
            except Exception as e:
                results[kw] = {"error": str(e)}
            
            processed_count += 1
            
        # Update State
        new_index = end_idx
        if new_index >= len(seeds):
            new_index = 0 # Reset
            
        state['current_index'] = new_index
        state['last_run'] = datetime.now().isoformat()
        save_json_file(STATE_FILE, state)
        
        # Output Results
        output_data = {
            "batch_processed": current_batch,
            "next_index": new_index,
            "results": results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "mode": "batch"
            }
        }
        
        # Save Raw Data
        raw_dir = os.path.join("output", "scouts", "raw")
        os.makedirs(raw_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_batch.json"
        save_path = os.path.join(raw_dir, filename)
        save_json_file(save_path, output_data)
        
        # Add file path to stdout output for AI to know where it is
        output_data["saved_to"] = save_path
        
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

def run_single_search(analyzer, keyword, limit, min_views):
    # Reusing the previous logic for single search
    df = analyzer.find_giant_killing_videos(
        keyword, 
        max_search_results=50, 
        min_views=min_views,
        max_subs=50000, 
        published_after=get_year_ago_iso(),
        video_type_filter="long", 
        min_duration=300  
    )
    
    if df.empty:
        print(json.dumps([]))
        return

    if 'gk_score' in df.columns:
        df = df.sort_values(by='gk_score', ascending=False)
    
    top_df = df.head(limit)
    output_cols = ['title', 'gk_score', 'view_count', 'subscriber_count', 'published_at', 'duration_sec', 'video_id', 'channel_title', 'tags']
    output_cols = [c for c in output_cols if c in top_df.columns]
    result_data = top_df[output_cols].to_dict(orient='records')
    for item in result_data:
        item['url'] = f"https://www.youtube.com/watch?v={item['video_id']}"
        
    print(json.dumps(result_data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
