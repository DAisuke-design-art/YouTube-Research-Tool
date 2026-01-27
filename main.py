import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
from core.analyzer import YouTubeAnalyzer
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="YouTube Research Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("YouTube Market Research Tool 🔍")
st.markdown("""
> **Goal:** Register fewer than 10k subscribers but find "Giant Killing" videos with over 10k views.
""")

# Sidebar
st.sidebar.header("Settings")
api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    st.sidebar.warning("API Key not found in .env")
    user_api_key = st.sidebar.text_input("Enter YouTube API Key", type="password")
    if user_api_key:
        api_key = user_api_key
else:
    st.sidebar.success("API Key loaded")

# Navigation
page = st.sidebar.radio("Mode", ["Giant Killing Finder", "Trend Monitor"])

# --- Helper Function for Date Config ---
def get_published_after(option):
    today = datetime.now()
    if option == "直近1年 (推奨)":
        return (today - timedelta(days=365)).isoformat("T") + "Z"
    elif option == "直近6ヶ月":
        return (today - timedelta(days=180)).isoformat("T") + "Z"
    elif option == "直近3ヶ月":
        return (today - timedelta(days=90)).isoformat("T") + "Z"
    elif option == "直近1ヶ月":
        return (today - timedelta(days=30)).isoformat("T") + "Z"
    else: # 全期間
        return None

if page == "Giant Killing Finder":
    st.header("ジャイアントキリング発掘 🏹")
    
    # --- Session State Initialization ---
    if 'gk_results' not in st.session_state:
        st.session_state.gk_results = None

    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("検索キーワード", placeholder="例: 明治 歴史")
    with col2:
        date_option = st.selectbox(
            "期間指定 (Freshness)", 
            ["直近1年 (推奨)", "直近6ヶ月", "直近3ヶ月", "全期間"]
        )
        # Convert choice to ISO format
        published_after = get_published_after(date_option)

    col_type, col_dummy = st.columns([1, 1]) 
    with col_type:
        video_type_option = st.radio(
            "動画タイプ",
            ["通常動画のみ (推奨)", "ショートのみ", "すべて"],
            horizontal=True
        )
        
        # Map to internal values & Set smart defaults
        video_type_filter = "all"
        min_duration_default = 0
        max_duration_default = 3600 # 1 hour
        
        if video_type_option == "通常動画のみ (推奨)":
            video_type_filter = "long"
            # Insight: 60s is technically long, but effectively noise. 
            # Defaulting to 120s (2 mins) to ensure "Research Quality" videos.
            min_duration_default = 120 
            max_duration_default = 7200 # 2 hours
        elif video_type_option == "ショートのみ":
            video_type_filter = "short"
            min_duration_default = 0
            max_duration_default = 60

    # Advanced Filters (Expander)
    with st.expander("詳細フィルタ (Advanced Filters)", expanded=True):
         c_dur1, c_dur2 = st.columns(2)
         with c_dur1:
             min_duration = st.number_input("最短尺 (秒) - これより短い動画を除外", value=min_duration_default, step=10, help="120秒以上に設定すると、質の低い動画を完全に排除できます。")
         with c_dur2:
             # Just a placeholder/display, passing None if easy, but let's pass explicit None if user wants 'Any'
             # For simplicity, let's keep it basic.
             pass

    col3, col4, col5 = st.columns(3)
    with col3:
        max_results = st.slider("分析対象数 (Max Results)", 10, 50, 50)
    with col4:
        min_views = st.number_input("最低再生数 (Min Views)", value=10000, step=1000)
    with col5:
        max_subs = st.number_input("最大登録者数 (Max Subscribers)", value=10000, step=1000)
    
    # Search Button
    if st.button("検索 & 分析開始 (Search & Analyze)"):
        if not api_key:
            st.error("APIキーが設定されていません。")
        else:
            with st.spinner(f"「{keyword}」を検索中... ({date_option}, {video_type_option})"):
                try:
                    analyzer = YouTubeAnalyzer(api_key)
                    df = analyzer.find_giant_killing_videos(
                        keyword, 
                        max_search_results=max_results,
                        min_views=min_views,
                        max_subs=max_subs,
                        published_after=published_after,
                        video_type_filter=video_type_filter,
                        min_duration=min_duration
                    )
                    # Save to Session State
                    st.session_state.gk_results = df
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # --- Display Results from Session State ---
    if st.session_state.gk_results is not None:
        df = st.session_state.gk_results
        
        # Clear Button
        if st.button("🗑️ 結果をクリア"):
             st.session_state.gk_results = None
             st.rerun()

        if df.empty:
            st.warning("条件に合う動画が見つかりませんでした。条件を緩めるか、検索数を増やしてみてください。")
        else:
            st.success(f"お宝動画を {len(df)} 件発見しました！")
            
            # --- Opportunity Map (Scatter Plot) ---
            st.subheader("市場分析マップ (Opportunity Map) 🗺️")
            st.markdown("縦軸が高いほど**需要（再生数）**があり、左にあるほど**ライバル不在（低登録者）**です。")
            st.markdown("つまり、**左上**にある動画ほど「お宝（Giant Killing）」です。")
            
            # Create Scatter Plot
            # log_x=True helps visualize subscribers better as they vary widely
            fig = px.scatter(
                df,
                x="subscriber_count",
                y="view_count",
                size="gk_score",
                color="gk_score",
                hover_name="title",
                hover_data={
                    "channel_title": True,
                    "published_at": True,
                    "view_count": ":,",
                    "subscriber_count": ":,",
                    "gk_score": True,
                    "video_id": False # Hide ID
                },
                labels={
                    "subscriber_count": "チャンネル登録者数 (Subscribers)",
                    "view_count": "再生回数 (Views)",
                    "gk_score": "GKスコア"
                },
                title="Giant Killing Opportunity Map",
                color_continuous_scale="Viridis", # or "Plasma", "Turbo"
                log_x=True, # Log scale for subscribers often makes sense
                log_y=True  # Log scale for views too
            )
            st.plotly_chart(fig, use_container_width=True)
            # --------------------------------------

            # Add URL column for clickable links (if not already there)
            if 'url' not in df.columns:
                 df['url'] = "https://www.youtube.com/watch?v=" + df['video_id']

            # Display Metrics
            for _, row in df.iterrows():
                with st.expander(f"{row['title']} (GKスコア: {row['gk_score']})"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(row['thumbnail'])
                    with c2:
                        st.markdown(f"**チャンネル:** {row['channel_title']} ({row['subscriber_count']:,} 人)")
                        st.markdown(f"**再生数:** {row['view_count']:,} 回")
                        st.markdown(f"**投稿日:** {row['published_at']}")
                        st.markdown(f"**動画タイプ:** {'Shorts (≦60s)' if row.get('duration_sec', 0) <= 60 else 'Video'}")
                        st.markdown(f"[YouTubeで見る]({row['url']})")
                        if 'tags' in row and row['tags']:
                             st.info(f"タグ: {', '.join(row['tags'][:5])}...")

            # Data Export
            st.subheader("データ出力 (Data Export)")
            col_dl1, col_dl2 = st.columns(2)
            
            # CSV
            csv = df.to_csv(index=False).encode('utf-8')
            col_dl1.download_button(
                label="CSVでダウンロード",
                data=csv,
                file_name='giant_killing_videos.csv',
                mime='text/csv',
            )
            
            # Markdown
            md = df.to_markdown(index=False)
            col_dl2.download_button(
                label="Markdownでダウンロード",
                data=md,
                file_name='giant_killing_videos.md',
                mime='text/markdown',
            )

            # Raw Data table
            st.subheader("生データ (Raw Data)")
            st.dataframe(
                df,
                column_config={
                    "url": st.column_config.LinkColumn("Video URL", display_text="Watch Video"),
                    "thumbnail": st.column_config.ImageColumn("Thumbnail"),
                },
            )
            
elif page == "Trend Monitor":
    st.header("トレンド監視 (Trend Monitor) 📈")
    
    # Category Map (Partial list of popular categories)
    # Source: https://gist.github.com/dgp/1b24bf2961521bd75d6c
    CATEGORIES = {
        "All (すべて)": None,
        "Film & Animation (映画とアニメ)": "1",
        "Autos & Vehicles (自動車と乗り物)": "2",
        "Music (音楽)": "10",
        "Pets & Animals (ペットと動物)": "15",
        "Sports (スポーツ)": "17",
        "Travel & Events (旅行とイベント)": "19",
        "Gaming (ゲーム)": "20",
        "People & Blogs (ブログ)": "22",
        "Comedy (コメディ)": "23",
        "Entertainment (エンタメ)": "24",
        "News & Politics (ニュースと政治)": "25",
        "Howto & Style (ハウツーとスタイル)": "26",
        "Education (教育)": "27",
        "Science & Technology (科学と技術)": "28",
    }
    
    col_cat, col_btn = st.columns([3, 1])
    with col_cat:
        selected_category_name = st.selectbox("カテゴリ選択 (Category)", options=list(CATEGORIES.keys()))
        selected_category_id = CATEGORIES[selected_category_name]
    
    with col_btn:
        st.write("") # Spacer
        st.write("") # Spacer
        tm_search = st.button("トレンド取得 (Fetch Trends)")

    if tm_search:
        if not api_key:
            st.error("APIキーが設定されていません。")
        else:
            with st.spinner("急上昇データを取得中..."):
                try:
                    analyzer = YouTubeAnalyzer(api_key)
                    # We can reuse the analyzer since we added the method there
                    df_trend = analyzer.get_trend_videos(category_id=selected_category_id)
                    
                    if df_trend.empty:
                        st.warning("データが取得できませんでした。時間をおいて試してください。")
                    else:
                        st.success(f"{len(df_trend)} 件のトレンド動画を取得しました！")
                        
                        # Add URL
                        if 'url' not in df_trend.columns:
                            df_trend['url'] = "https://www.youtube.com/watch?v=" + df_trend['video_id']

                        # Display
                        for _, row in df_trend.iterrows():
                            # Highlight logic? Maybe
                            with st.expander(f"{row['title']} (再生: {row['view_count']:,})"):
                                c1, c2 = st.columns([1, 2])
                                with c1:
                                    st.image(row['thumbnail'])
                                with c2:
                                    st.markdown(f"**チャンネル:** {row['channel_title']} ({row['subscriber_count']:,} 人)")
                                    st.markdown(f"**再生数:** {row['view_count']:,} 回")
                                    st.markdown(f"**投稿日:** {row['published_at']}")
                                    st.markdown(f"**GKスコア:** {row['gk_score']}")
                                    st.markdown(f"[YouTubeで見る]({row['url']})")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
