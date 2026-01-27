import pandas as pd
import plotly.express as px

print("Testing Visualization Logic...")

# Create dummy data
data = {
    "title": ["Video A", "Video B", "Video C"],
    "subscriber_count": [1000, 50000, 100],
    "view_count": [50000, 10000, 5000],
    "gk_score": [50.0, 0.2, 50.0],
    "channel_title": ["Ch A", "Ch B", "Ch C"],
    "published_at": ["2023-01-01", "2023-01-02", "2023-01-03"],
    "video_id": ["v1", "v2", "v3"]
}
df = pd.DataFrame(data)

try:
    print("Creating Scatter Plot...")
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
            "video_id": False
        },
        labels={
            "subscriber_count": "Channels",
            "view_count": "Views",
            "gk_score": "GK Score"
        },
        title="Test Map",
        log_x=True,
        log_y=True
    )
    # fig.show() # Cannot show in headless, but creation means success
    print("Scatter Plot created successfully.")

except Exception as e:
    print(f"Error creating plot: {e}")
    exit(1)
