import os
from urllib.parse import urlparse, parse_qs
from pytubefix import YouTube

# 範例影片 URL，請依需求替換
URL = r"https://www.youtube.com/watch?v=0kXQCKJjDlw&t=1146s&ab_channel=Gooaye%E8%82%A1%E7%99%8C"

def get_video_id(url):
    """
    從 YouTube 影片 URL 中取得影片 ID，支援多種 URL 格式。
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["youtu.be"]:
        return parsed_url.path[1:]  # 去除前面的 '/'
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        if parsed_url.path == "/watch":
            query = parse_qs(parsed_url.query)
            return query.get("v", [None])[0]
        elif parsed_url.path.startswith("/embed/"):
            return parsed_url.path.split("/")[2]
        elif parsed_url.path.startswith("/v/"):
            return parsed_url.path.split("/")[2]
    return None

def download_audio(video_id, output_dir):
    """
    使用 pytubefix 下載影片的音訊部分，
    取消轉換成 MP3，直接回傳原始下載檔案。
    """
    try:
        yt_url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(yt_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        if audio_stream is None:
            print("找不到適合的音訊串流。")
            return None
        print("正在下載音訊...")
        audio_file = audio_stream.download(output_path=output_dir)
        print(f"下載完成：{audio_file}")
        return audio_file
    except Exception as e:
        print(f"下載音訊發生錯誤：{str(e)}")
        return None

def download_youtube_voice(url):
    """
    主函式：從 YouTube 影片 URL 中取得影片 ID，
    下載音訊並保存原始檔案。
    """
    video_id = get_video_id(url)
    if not video_id:
        print("無法從 URL 中解析出影片 ID。")
        return
    
    # 建立以影片 ID 命名的目錄，用於存放下載檔案
    output_dir = video_id
    os.makedirs(output_dir, exist_ok=True)
    
    audio_file = download_audio(video_id, output_dir)
    if audio_file:
        print(f"已成功下載音訊：{audio_file}")
    else:
        print("下載失敗。")

if __name__ == "__main__":
    download_youtube_voice(URL)