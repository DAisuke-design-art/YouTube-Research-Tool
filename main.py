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
                # Format Duration
                duration = "N/A"
                raw_sec = row.get('duration_sec', 0)
                if raw_sec > 0:
                    m, s = divmod(int(raw_sec), 60)
                    h, m = divmod(m, 60)
                    if h > 0:
                        duration = f"{h}:{m:02d}:{s:02d}"
                    else:
                        duration = f"{m}:{s:02d}"

                # Label
                label = f"[{duration}] {row['title']} (GKスコア: {row['gk_score']})"
                
                with st.expander(label):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(row['thumbnail'])
                    with c2:
                        st.markdown(f"**チャンネル:** {row['channel_title']} ({row['subscriber_count']:,} 人)")
                        st.markdown(f"**再生数:** {row['view_count']:,} 回")
                        st.markdown(f"**投稿日:** {row['published_at']}")
                        st.markdown(f"**動画時間:** {duration} ({'Shorts' if raw_sec <= 65 else 'Video'})")
                        st.markdown(f"[YouTubeで見る]({row['url']})")
                        if 'tags' in row and row['tags']:
                             st.info(f"タグ: {', '.join(row['tags'][:5])}...")

            # --- Prepare Data for Display/Export (Japanese Headers) ---
            # AI (GEM3) understands Japanese headers perfectly fine.
            # actually better for context.
            
            df_display = df.copy()
            
            # Select and Rename Columns
            columns_map = {
                "title": "タイトル(Title)",
                "channel_title": "チャンネル名(Channel)",
                "view_count": "再生数(Views)",
                "subscriber_count": "登録者数(Subscribers)",
                "gk_score": "GKスコア(再生数÷登録者数_高=企画勝)",
                "published_at": "投稿日(Published)",
                "duration_sec": "動画時間_秒(Duration_Sec)",
                "url": "動画URL(URL)",
                "tags": "タグ(Tags)",
                "video_id": "動画ID",
                "channel_id": "チャンネルID",
                "like_count": "高評価数",
                "comment_count": "コメント数",
                "video_count": "チャンネル総動画数"
            }
            
            # Reorder for better readability
            display_order = [
                "title", "view_count", "subscriber_count", "gk_score", 
                "channel_title", "published_at", "duration_sec", "url", 
                "tags", "like_count", "comment_count"
            ]
            # Add remaining keys if they exist in df but not in display_order
            remaining = [c for c in df.columns if c not in display_order and c in columns_map]
            final_order = display_order + remaining
            
            # Filter columns that actually exist in the dataframe
            final_cols = [c for c in final_order if c in df.columns]
            
            df_display = df_display[final_cols].rename(columns=columns_map)
            
            # -------------------------------------------------------

            # Data Export
            st.subheader("データ出力 (Data Export)")
            col_dl1, col_dl2 = st.columns(2)
            
            # Generate Filename
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            # Sanitize keyword
            safe_keyword = keyword.replace(" ", "_").replace("　", "_")
            # Prefix GK for Giant Killing
            file_base = f"GK_{now_str}_{safe_keyword}"
            
            # CSV
            csv = df_display.to_csv(index=False).encode('utf-8_sig') # utf-8_sig for Excel compatibility
            col_dl1.download_button(
                label="CSVでダウンロード",
                data=csv,
                file_name=f'{file_base}.csv',
                mime='text/csv',
            )
            
            # Markdown
            md = df_display.to_markdown(index=False)
            col_dl2.download_button(
                label="Markdownでダウンロード",
                data=md,
                file_name=f'{file_base}.md',
                mime='text/markdown',
            )

            # Raw Data table
            st.subheader("生データ (Raw Data)")
            # We don't really need special config if we renamed columns, 
            # except maybe formatting numbers or links.
            st.dataframe(
                df_display,
                column_config={
                    "動画URL": st.column_config.LinkColumn("動画URL", display_text="Watch"),
                },
                hide_index=True
            )
            
elif page == "Trend Monitor":
    st.header("トレンド監視 & 企画発掘 (Trend & Idea Mining) 📈")
    
    # Mode Selection (Tabs)
    tab_idea, tab_cat = st.tabs(["💡 企画キーワード発掘 (Idea Mining)", "📊 カテゴリ急上昇 (Category Trends)"])

    # --- TAB 1: Category Trends ---
    with tab_cat:
        # Category Map (Partial list of popular categories)
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
            
            # Duration Filter Slider
            tm_min_duration = st.slider(
                "最小動画時間 (分) - Quality Filter", 
                min_value=0, 
                max_value=20, 
                value=5, 
                step=1,
                help="指定した分数未満の動画（中途半端な尺）を排除します。推奨: 3〜5分"
            )
        
        with col_btn:
            st.write("") # Spacer
            st.write("") # Spacer
            st.write("") # Spacer (Align with slider)
            tm_search = st.button("トレンド取得 (Fetch Trends)")

        if tm_search:
            if not api_key:
                st.error("APIキーが設定されていません。")
            else:
                with st.spinner("急上昇データを取得中..."):
                    try:
                        analyzer = YouTubeAnalyzer(api_key)
                        df_trend = analyzer.get_trend_videos(
                            category_id=selected_category_id,
                            min_duration=tm_min_duration # Pass user filter
                        )
                        
                        if df_trend.empty:
                            st.warning(f"データが取得できませんでした。（条件: {tm_min_duration}分以上）")
                        else:
                            st.success(f"{len(df_trend)} 件のトレンド動画を取得しました！")
                            if 'url' not in df_trend.columns:
                                df_trend['url'] = "https://www.youtube.com/watch?v=" + df_trend['video_id']

                            for _, row in df_trend.iterrows():
                                # Format Duration
                                duration = "N/A"
                                raw_sec = row['duration_sec']
                                if raw_sec > 0:
                                    m, s = divmod(int(raw_sec), 60)
                                    h, m = divmod(m, 60)
                                    if h > 0:
                                        duration = f"{h}:{m:02d}:{s:02d}"
                                    else:
                                        duration = f"{m}:{s:02d}"

                                # Create a label for the expander
                                gk_val = row['gk_score']
                                prefix = "🔥 " if gk_val >= 10 else ""
                                date_str = row['published_at'][:10]
                                label = f"{prefix}[{duration}] {row['title']} (📅 {date_str} | GK: {gk_val} | 👁️ {row['view_count']:,})"

                                with st.expander(label):
                                    c1, c2 = st.columns([1, 2])
                                    with c1:
                                        st.image(row['thumbnail'])
                                    
                                    with c2:
                                        st.markdown(f"**チャンネル:** {row['channel_title']} ({row['subscriber_count']:,} 人)")
                                        st.markdown(f"**再生数:** {row['view_count']:,} 回")
                                        st.markdown(f"**投稿日:** {row['published_at']}")
                                        st.markdown(f"**動画時間:** {duration} ({'Shorts' if raw_sec <= 65 else 'Video'})")
                                        st.markdown(f"**GKスコア:** {row['gk_score']}")
                                        st.markdown(f"[YouTubeで見る]({row['url']})")
                    
                            # Data Export
                            st.divider()
                            st.subheader("トレンドデータ出力")
                            
                            df_trend_display = df_trend.copy()
                            columns_map = {
                                "title": "タイトル(Title)", 
                                "channel_title": "チャンネル名(Channel)", 
                                "view_count": "再生数(Views)",
                                "subscriber_count": "登録者数(Subscribers)", 
                                "gk_score": "GKスコア(再生数÷登録者数_高=企画勝)", 
                                "published_at": "投稿日(Published)",
                                "duration_sec": "動画時間_秒(Duration_Sec)", 
                                "url": "動画URL(URL)", 
                                "tags": "タグ(Tags)",
                            }
                            # Cleanup
                            extra_cols = [c for c in df_trend.columns if c in columns_map]
                            df_trend_display = df_trend_display[extra_cols].rename(columns=columns_map)

                            # CSV DL
                            now_str = datetime.now().strftime('%Y%m%d_%H%M')
                            cat_slug = selected_category_name.split(" (")[0].replace(" & ", "_").replace(" ", "_")
                            # Prefix TL for Trend List
                            file_base_trend = f"TL_{now_str}_{cat_slug}"
                            
                            csv_t = df_trend_display.to_csv(index=False).encode('utf-8_sig')
                            st.download_button(
                                "CSVでダウンロード", csv_t, f'{file_base_trend}.csv', 'text/csv'
                            )

                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- TAB 2: Keyword Idea Mining ---
    with tab_idea:
        st.subheader("💡 企画キーワード発掘 (Idea Mining)")
        st.markdown("キーワードに関連する動画から**「よく使われているタグ（バズる要素）」**を抽出します。")
        
        # Layout: Keyword Input | Video Type | Button
        col_kw, col_type, col_go = st.columns([3, 2, 1])
        
        with col_kw:
            idea_keyword = st.text_input("発掘キーワード", placeholder="例: 歴史 寿司")
        
        with col_type:
            # Video Type Selector
            video_type_label = st.radio(
                "動画タイプ (Target)",
                ("Long Video (長尺)", "Shorts (ショート)", "All (すべて)"),
                horizontal=True
            )
            # Map label to code
            type_map = {
                "Long Video (長尺)": "long",
                "Shorts (ショート)": "short",
                "All (すべて)": "all"
            }
            selected_type = type_map[video_type_label]
            
            # Duration Filter (Idea Mining)
            im_min_duration = st.slider(
                "最小動画時間 (分) - Quality Filter", 
                min_value=0, 
                max_value=20, 
                value=5, 
                step=1,
                help="指定した分数未満の動画を排除します。"
            )

        with col_go:
            st.write("") # Spacer
            st.write("") # Spacer
            st.write("") # Spacer
            idea_search = st.button("発掘開始 (Start Mining)")

        if idea_search and idea_keyword:
            if not api_key:
                st.error("API Key missing")
            else:
                with st.spinner(f"「{idea_keyword}」のバズ要素を分析中... ({video_type_label})"):
                    try:
                        analyzer = YouTubeAnalyzer(api_key)
                        # Use same search logic but maybe looser filters to get broad ideas
                        # Default to 50 results, recent 1 year for relevance
                        today = datetime.now()
                        one_year_ago = (today - timedelta(days=365)).isoformat("T") + "Z"
                        
                        df_idea = analyzer.find_giant_killing_videos(
                            idea_keyword, 
                            max_search_results=50,
                            published_after=one_year_ago,
                            min_views=1000, 
                            max_subs=10000000,
                            video_type_filter=selected_type, # Pass user selection
                            min_duration=im_min_duration * 60 # Convert min -> sec
                        )
                        
                        if df_idea.empty:
                            st.warning("動画が見つかりませんでした。")
                        else:
                            st.success(f"{len(df_idea)} 件の動画からタグを分析しました！")
                            # Analyze Tags
                            tag_df = analyzer.analyze_tags(df_idea)
                            
                            # SAVE TO SESSION STATE
                            st.session_state['im_df_idea'] = df_idea
                            st.session_state['im_tag_df'] = tag_df
                            st.session_state['im_keyword'] = idea_keyword
                            st.session_state['im_type'] = video_type_label

                    except Exception as e:
                        st.error(f"Error during analysis: {e}")

        # DISPLAY RESULTS (Check Session State)
        if 'im_df_idea' in st.session_state and not st.session_state['im_df_idea'].empty:
            df_idea = st.session_state['im_df_idea']
            tag_df = st.session_state['im_tag_df']
            
            # Show active result context if it wasn't just searched
            if not idea_search: 
                st.info(f"Displaying results for: {st.session_state.get('im_keyword', 'Unknown')} ({st.session_state.get('im_type', 'Unknown')})")

            if not tag_df.empty:
                st.subheader("🚀 バズるキーワード候補 (Tag Cloud)")
                # Bar Chart
                fig_tags = px.bar(
                    tag_df.head(20), 
                    x='count', 
                    y='tag', 
                    orientation='h',
                    title=f"'{st.session_state.get('im_keyword')}' 頻出タグ Top 20",
                    labels={'count': '出現回数', 'tag': 'タグ'},
                    height=600
                )
                fig_tags.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_tags, use_container_width=True)
                
                # Show Tag List
                with st.expander("全タグリストを表示"):
                                    st.dataframe(tag_df)
            else:
                st.info("タグ情報が取得できませんでした。")
            
            st.divider()
            st.subheader("参考動画リスト (Results)")
            
            # Add URL if missing
            if 'url' not in df_idea.columns:
                df_idea['url'] = "https://www.youtube.com/watch?v=" + df_idea['video_id']

            for _, row in df_idea.iterrows():
                # Format Duration
                duration = "N/A"
                raw_sec = row['duration_sec']
                if raw_sec > 0:
                    m, s = divmod(int(raw_sec), 60)
                    h, m = divmod(m, 60)
                    if h > 0:
                        duration = f"{h}:{m:02d}:{s:02d}"
                    else:
                        duration = f"{m}:{s:02d}"

                # Create a label for the expander
                gk_val = row['gk_score']
                prefix = "🔥 " if gk_val >= 10 else ""
                # Include Duration and Date in label
                date_str = row['published_at'][:10]
                label = f"{prefix}[{duration}] {row['title']} (📅 {date_str} | GK: {gk_val} | 👁️ {row['view_count']:,})"
                
                with st.expander(label):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if row['thumbnail']:
                            st.image(row['thumbnail'])
                    with c2:
                        st.markdown(f"**チャンネル:** {row['channel_title']} ({row['subscriber_count']:,} 人)")
                        st.markdown(f"**再生数:** {row['view_count']:,} 回")
                        st.markdown(f"**投稿日:** {row['published_at']}")
                        st.markdown(f"**動画時間:** {duration} ({'Shorts' if raw_sec <= 65 else 'Video'})")
                        st.markdown(f"[YouTubeで見る]({row['url']})")
                    
                    # Tags Display
                    if 'tags' in row and isinstance(row['tags'], list) and row['tags']:
                        tags_str = ", ".join(row['tags'])
                        st.info(f"タグ: {tags_str}")
                    else:
                        st.caption("タグ情報なし")
            
            # --- Data Export (Idea Mining) ---
            st.divider()
            st.subheader("発掘データ出力 (Data Export)")
            
            df_idea_display = df_idea.copy()
            columns_map_idea = {
                "title": "タイトル(Title)", 
                "channel_title": "チャンネル名(Channel)", 
                "view_count": "再生数(Views)",
                "subscriber_count": "登録者数(Subscribers)", 
                "gk_score": "GKスコア(再生数÷登録者数_高=企画勝)", 
                "published_at": "投稿日(Published)",
                "duration_sec": "動画時間_秒(Duration_Sec)", 
                "url": "動画URL(URL)", 
                "tags": "タグ(Tags)",
            }
            # Cleanup columns
            extra_cols_i = [c for c in df_idea.columns if c in columns_map_idea]
            df_idea_display = df_idea_display[extra_cols_i].rename(columns=columns_map_idea)
            
            # Generate Filename
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            safe_kw = st.session_state.get('im_keyword', 'result').replace(" ", "_").replace("　", "_")
            # Prefix IM for Idea Mining
            file_base_idea = f"IM_{now_str}_{safe_kw}_{st.session_state.get('im_type', 'all')}"
            
            # CSV
            csv_i = df_idea_display.to_csv(index=False).encode('utf-8_sig')
            st.download_button(
                "CSVでダウンロード", csv_i, f'{file_base_idea}.csv', 'text/csv'
            )
