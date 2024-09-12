import streamlit as st
import json
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build

# Thay YOUR_API_KEY với API key của bạn
YOUTUBE_API_KEY = "AIzaSyCj-mohmj7zsBs7o-0TYfY3_zfVygSN52Y"


def get_channel_id_by_username(username):
    """Lấy Channel ID từ tên người dùng tùy chỉnh."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Sử dụng phương thức 'search' để tìm kiếm kênh từ tên người dùng tùy chỉnh
    request = youtube.search().list(
        part="snippet", q=username, type="channel", maxResults=1
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        return response["items"][0]["snippet"]["channelId"]
    else:
        st.error("Không thể tìm thấy Channel ID từ URL đã nhập.")
        return None


def get_video_ids_from_channel(username):
    channel_id = get_channel_id_by_username(username)
    if not channel_id:
        return []

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    video_ids = []
    next_page_token = None

    while True:
        request = youtube.search().list(
            part="id", channelId=channel_id, maxResults=50, pageToken=next_page_token
        )
        response = request.execute()
        for item in response["items"]:
            if item["id"]["kind"] == "youtube#video":
                video_ids.append(item["id"]["videoId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids


def get_video_title(video_id):
    """Lấy tiêu đề video từ video ID."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    return response["items"][0]["snippet"]["title"]


def save_subtitles_to_json(video_id, title):
    """Lưu phụ đề vào file JSON với tiêu đề video."""
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcripts.find_transcript(["vi"])  # Tìm phụ đề tiếng Việt
        subtitle_data = transcript.fetch()
        subtitles_text = " ".join([item["text"] for item in subtitle_data])

        # Tạo một dictionary cho video này
        video_data = {"title": title, "subtitles": subtitles_text}
        return video_data
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi tải phụ đề cho video ID {video_id}: {e}")
        return None


# Giao diện người dùng với Streamlit
st.title("Tải Phụ Đề cho Toàn Bộ Video Từ Kênh YouTube")

channel_url = st.text_input("Nhập URL của kênh YouTube", "title@@1")

if st.button("Tải và Lưu Phụ Đề"):
    video_ids = get_video_ids_from_channel(channel_url)
    st.write(f"Đã tìm thấy {len(video_ids)} video từ kênh.")

    all_videos_data = []

    for video_id in video_ids:
        title = get_video_title(video_id)
        video_data = save_subtitles_to_json(video_id, title)
        if video_data:
            all_videos_data.append(video_data)

    # Lưu tất cả các dữ liệu vào file JSON
    with open("videos_subtitles.json", "w", encoding="utf-8") as f:
        json.dump(all_videos_data, f, ensure_ascii=False, indent=4)

    st.success("Phụ đề đã được lưu vào file `videos_subtitles.json`!")
