import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from core.analyzer import YouTubeAnalyzer

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

if page == "Giant Killing Finder":
    st.header("Giant Killing Finder 🏹")
    
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("Search Keyword", placeholder="e.g. 明治 歴史")
    with col2:
        max_results = st.slider("Max Results to Analyze", 10, 50, 50)
        
    col3, col4 = st.columns(2)
    with col3:
        min_views = st.number_input("Min Views", value=10000, step=1000)
    with col4:
        max_subs = st.number_input("Max Subscribers", value=10000, step=1000)
    
    if st.button("Search & Analyze"):
        if not api_key:
            st.error("Please provide an API Key to proceed.")
        else:
            with st.spinner(f"Searching for '{keyword}' and analyzing channel data..."):
                try:
                    analyzer = YouTubeAnalyzer(api_key)
                    df = analyzer.find_giant_killing_videos(
                        keyword, 
                        max_search_results=max_results,
                        min_views=min_views,
                        max_subs=max_subs
                    )
                    
                    if df.empty:
                        st.warning("No videos found matching the criteria. Try loosening the filters or increasing search results.")
                    else:
                        st.success(f"Found {len(df)} Giant Killing videos!")
                        
                        # Add URL column for clickable links
                        df['url'] = "https://www.youtube.com/watch?v=" + df['video_id']

                        # Display Metrics
                        for _, row in df.iterrows():
                            with st.expander(f"{row['title']} (GK Score: {row['gk_score']})"):
                                c1, c2 = st.columns([1, 2])
                                with c1:
                                    st.image(row['thumbnail'])
                                with c2:
                                    st.markdown(f"**Channel:** {row['channel_title']} ({row['subscriber_count']:,} subs)")
                                    st.markdown(f"**Views:** {row['view_count']:,}")
                                    st.markdown(f"**Published:** {row['published_at']}")
                                    st.markdown(f"[Watch on YouTube]({row['url']})")
                                    st.info(f"Tags: {', '.join(row['tags'][:5])}...")

                        # Data Export
                        st.subheader("Data Export")
                        col_dl1, col_dl2 = st.columns(2)
                        
                        # CSV
                        csv = df.to_csv(index=False).encode('utf-8')
                        col_dl1.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name='giant_killing_videos.csv',
                            mime='text/csv',
                        )
                        
                        # Markdown
                        md = df.to_markdown(index=False)
                        col_dl2.download_button(
                            label="Download Markdown",
                            data=md,
                            file_name='giant_killing_videos.md',
                            mime='text/markdown',
                        )

                        # Raw Data table
                        st.subheader("Raw Data")
                        st.dataframe(
                            df,
                            column_config={
                                "url": st.column_config.LinkColumn("Video URL", display_text="Watch Video"),
                                "thumbnail": st.column_config.ImageColumn("Thumbnail"),
                            },
                        )
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            
elif page == "Trend Monitor":
    st.header("Trend Monitor 📈")
    st.info("Coming soon in the next update!")
