import os
import time
import yt_dlp
import whisper
import googleapiclient.discovery
from openai import OpenAI
from dotenv import load_dotenv
from opencc import OpenCC  # 新增簡繁轉換套件

# 載入環境變數
load_dotenv()

# 初始化簡繁轉換器
cc = OpenCC('s2t')

# 設定API金鑰
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
        try:
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
                
            time.sleep(1)  # API速率限制保護
            
        except Exception as e:
            print(f"獲取影片ID時發生錯誤: {str(e)}")
            break
    
    return video_ids

def extract_audio(video_id):
    """從影片中提取音訊(直接下載音訊檔)"""
    audio_path = os.path.join(OUTPUT_DIR, f"{video_id}.mp3")
    
    if os.path.exists(audio_path):
        print(f"音訊 {video_id}.mp3 已存在，跳過提取")
        return audio_path
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(OUTPUT_DIR, f"{video_id}"),
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    except Exception as e:
        print(f"音訊下載失敗: {str(e)}")
        return None
    
    return audio_path

def transcribe_with_whisper(model, audio_path, video_id):
    """使用Whisper模型進行轉譯並轉換為繁體中文"""
    print(f"使用Whisper轉譯 {video_id}...")
    try:
        result = model.transcribe(audio_path, language="zh")
        traditional_text = cc.convert(result["text"])
        
        transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}_whisper.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(traditional_text)
        return transcript_path
    except Exception as e:
        print(f"Whisper轉譯失敗: {str(e)}")
        return None

def transcribe_with_openai(audio_path, video_id):
    """使用OpenAI API進行轉譯並轉換為繁體中文"""
    print(f"使用OpenAI轉譯 {video_id}...")
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 檢查文件大小
        file_size = os.path.getsize(audio_path)
        if file_size > 25 * 1024 * 1024:
            print("檔案超過25MB，無法使用OpenAI API轉譯")
            return None
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh",
                response_format="text"
            )
        
        traditional_transcript = cc.convert(transcript)
        transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}_openai.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(traditional_transcript)
        return transcript_path
    except Exception as e:
        print(f"OpenAI轉譯失敗: {str(e)}")
        return None

def main():
    # 預加載Whisper模型
    print("正在加載Whisper模型...")
    whisper_model = whisper.load_model("large")
    
    # 獲取頻道ID
    print(f"\n正在解析頻道URL: {CHANNEL_URL}")
    try:
        channel_id = get_channel_id(CHANNEL_URL)
        print(f"頻道ID獲取成功: {channel_id}")
    except Exception as e:
        print(f"頻道ID獲取失敗: {str(e)}")
        return
    
    # 獲取所有影片ID
    print("\n正在獲取影片清單...")
    try:
        video_ids = get_all_video_ids(channel_id)
        print(f"共找到 {len(video_ids)} 部影片")
    except Exception as e:
        print(f"影片清單獲取失敗: {str(e)}")
        return
    
    # 處理每個影片
    total_videos = len(video_ids)
    for idx, video_id in enumerate(video_ids, 1):
        print(f"\n正在處理第 {idx}/{total_videos} 部影片 ({video_id})")
        
        # 下載音訊
        audio_path = extract_audio(video_id)
        if not audio_path or not os.path.exists(audio_path):
            print("音訊檔案不存在，跳過此影片")
            continue
        
        # 轉譯作業
        whisper_transcript = transcribe_with_whisper(whisper_model, audio_path, video_id)
        openai_transcript = transcribe_with_openai(audio_path, video_id)
        
        # 顯示結果
        transcripts = [t for t in [whisper_transcript, openai_transcript] if t]
        print(f"完成轉譯 ({len(transcripts)} 個版本)")
        
        # 清理暫存音訊檔
        try:
            os.remove(audio_path)
            print("已清理暫存音訊檔")
        except:
            pass
        
        time.sleep(1)  # API冷卻時間

if __name__ == "__main__":
    main()