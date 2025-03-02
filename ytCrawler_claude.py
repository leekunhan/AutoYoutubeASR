import os
import time
import yt_dlp
import whisper
import googleapiclient.discovery
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定API金鑰（請將這些放在.env文件中）
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 設定頻道URL和輸出目錄
CHANNEL_URL = "https://www.youtube.com/@Gooaye"
OUTPUT_DIR = "gooaye_videos"
TRANSCRIPTS_DIR = "gooaye_transcripts"

# 建立輸出目錄
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

def get_channel_id(url):
    """從頻道URL獲取頻道ID"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('id')

def get_all_video_ids(channel_id):
    """獲取頻道的所有影片ID"""
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    video_ids = []
    next_page_token = None
    
    while True:
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=50,
            type="video",
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response.get("items", []):
            video_ids.append(item["id"]["videoId"])
        
        next_page_token = response.get("nextPageToken")
        
        if not next_page_token:
            break
        
        # 避免超過YouTube API限制
        time.sleep(1)
    
    return video_ids

def download_video(video_id):
    """下載特定ID的影片"""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
    
    if os.path.exists(output_path):
        print(f"影片 {video_id} 已存在，跳過下載")
        return output_path
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    
    return output_path

def transcribe_with_whisper(audio_path, video_id):
    """使用Whisper模型進行轉譯（本地）"""
    print(f"使用Whisper本地模型轉譯 {video_id}...")
    # 載入中文優化的模型
    model = whisper.load_model("large")
    result = model.transcribe(audio_path, language="zh")
    
    # 保存轉譯文本
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}_whisper.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(result["text"])
    
    return transcript_path

def transcribe_with_openai(audio_path, video_id):
    """使用OpenAI API進行轉譯"""
    print(f"使用OpenAI API轉譯 {video_id}...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 檢查文件大小
    file_size = os.path.getsize(audio_path)
    # 如果檔案大於25MB (OpenAI API限制)
    if file_size > 25 * 1024 * 1024:
        print(f"檔案超過25MB，無法使用OpenAI API直接轉譯")
        return None
    
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="zh",
            response_format="text"
        )
    
    # 保存轉譯文本
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}_openai.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    return transcript_path

def extract_audio(video_path, video_id):
    """從影片中提取音訊"""
    audio_path = os.path.join(OUTPUT_DIR, f"{video_id}.mp3")
    
    if os.path.exists(audio_path):
        print(f"音訊 {video_id}.mp3 已存在，跳過提取")
        return audio_path
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': os.path.join(OUTPUT_DIR, f"{video_id}"),
        'quiet': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    
    return audio_path

def main():
    # 獲取頻道ID
    print(f"正在獲取頻道ID: {CHANNEL_URL}")
    channel_id = get_channel_id(CHANNEL_URL)
    print(f"頻道ID: {channel_id}")
    
    # 獲取所有影片ID
    print("正在獲取頻道所有影片ID...")
    video_ids = get_all_video_ids(channel_id)
    print(f"找到 {len(video_ids)} 個影片")
    
    # 為每個影片進行下載和轉譯
    for i, video_id in enumerate(video_ids):
        print(f"\n處理影片 {i+1}/{len(video_ids)}: {video_id}")
        
        # 提取音訊檔案
        audio_path = extract_audio(None, video_id)
        
        # 使用不同的模型進行轉譯
        try:
            # 嘗試使用本地Whisper模型（效果較好但需要下載模型）
            whisper_transcript = transcribe_with_whisper(audio_path, video_id)
            print(f"Whisper轉譯完成: {whisper_transcript}")
        except Exception as e:
            print(f"Whisper轉譯錯誤: {str(e)}")
        
        try:
            # 嘗試使用OpenAI API
            openai_transcript = transcribe_with_openai(audio_path, video_id)
            if openai_transcript:
                print(f"OpenAI轉譯完成: {openai_transcript}")
        except Exception as e:
            print(f"OpenAI轉譯錯誤: {str(e)}")
        
        # 避免過度請求API
        time.sleep(2)

if __name__ == "__main__":
    main()