import os
import argparse
from urllib.parse import urlparse, parse_qs
from pytubefix import YouTube, Playlist

# 範例影片 URL
URL = ""
# 範例播放清單 URL
PLAYLIST_URL = ""

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
        
        # 只使用影片標題作為檔案名
        filename = yt.title
        # 替換文件名中的非法字符
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            filename = filename.replace(char, '_')
        
        # 添加適當的副檔名
        file_extension = audio_stream.subtype
        if not filename.endswith(f".{file_extension}"):
            filename = f"{filename}.{file_extension}"
        
        audio_file = audio_stream.download(output_path=output_dir, filename=filename)
        print(f"下載完成：{audio_file}")
        return audio_file
    except Exception as e:
        print(f"下載音訊發生錯誤：{str(e)}")
        return None

def download_youtube_voice(url, output_dir="voices"):
    """
    主函式：從 YouTube 影片 URL 中取得影片 ID，
    下載音訊並保存原始檔案到指定資料夾中。
    
    Args:
        url (str): YouTube 影片的 URL
        output_dir (str): 輸出資料夾路徑
    """
    video_id = get_video_id(url)
    if not video_id:
        print("無法從 URL 中解析出影片 ID。")
        return
    
    # 建立輸出資料夾
    os.makedirs(output_dir, exist_ok=True)
    
    # 直接下載到指定資料夾
    audio_file = download_audio(video_id, output_dir)
    if audio_file:
        print(f"已成功下載音訊：{audio_file}")
    else:
        print("下載失敗。")

def download_playlist(playlist_url, output_dir="voices", limit=0):
    """
    下載整個 YouTube 播放清單中的所有音訊檔案。
    
    Args:
        playlist_url (str): YouTube 播放清單的 URL
        output_dir (str): 輸出資料夾路徑
        limit (int): 限制下載的影片數量，0表示不限制
    """
    try:
        # 建立播放清單物件
        playlist = Playlist(playlist_url)
        
        # 建立播放清單專用資料夾
        playlist_title = playlist.title
        # 替換資料夾名稱中的非法字符
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            playlist_title = playlist_title.replace(char, '_')
        
        playlist_dir = os.path.join(output_dir, playlist_title)
        os.makedirs(playlist_dir, exist_ok=True)
        
        print(f"開始下載播放清單：{playlist.title}")
        print(f"播放清單共有 {len(playlist.video_urls)} 個影片")
        
        # 下載每個影片的音訊
        successful_downloads = 0
        for index, video_url in enumerate(playlist.video_urls):
            video_id = get_video_id(video_url)
            if not video_id:
                print(f"無法從 URL 中解析出影片 ID：{video_url}")
                continue
            
            if limit > 0 and successful_downloads >= limit:
                break
            
            print(f"正在下載第 {index+1}/{len(playlist.video_urls)} 個影片...")
            audio_file = download_audio(video_id, playlist_dir)
            
            if audio_file:
                successful_downloads += 1
                print(f"已成功下載：{os.path.basename(audio_file)}")
            else:
                print(f"下載失敗：{video_url}")
        
        print(f"播放清單下載完成！成功下載 {successful_downloads}/{len(playlist.video_urls)} 個音訊檔案")
        print(f"檔案保存在：{os.path.abspath(playlist_dir)}")
        
    except Exception as e:
        print(f"下載播放清單時發生錯誤：{str(e)}")

def is_playlist_url(url):
    """
    判斷 URL 是否為播放清單 URL
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        if parsed_url.path == "/playlist":
            return True
        elif "list=" in parsed_url.query:
            return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='下載 YouTube 影片或播放清單的音訊')
    parser.add_argument('url', nargs='?', default=None, help='YouTube 影片或播放清單的 URL')
    parser.add_argument('--playlist', action='store_true', help='強制將 URL 視為播放清單')
    parser.add_argument('--video', action='store_true', help='強制將 URL 視為單一影片')
    parser.add_argument('--output', '-o', default='voices', help='指定輸出資料夾')
    parser.add_argument('--limit', '-l', type=int, default=0, help='限制下載的影片數量，0表示不限制')
    
    args = parser.parse_args()
    
    # 如果沒有提供 URL，使用預設值
    url = args.url
    if not url:
        if args.playlist:
            url = PLAYLIST_URL
            print(f"使用預設播放清單 URL: {url}")
        else:
            url = URL
            print(f"使用預設影片 URL: {url}")
    
    # 建立輸出資料夾
    os.makedirs(args.output, exist_ok=True)
    
    # 根據參數或 URL 類型決定下載方式
    if args.playlist or (is_playlist_url(url) and not args.video):
        print("正在下載播放清單...")
        download_playlist(url, args.output, args.limit)
    else:
        print("正在下載單一影片...")
        download_youtube_voice(url, args.output)