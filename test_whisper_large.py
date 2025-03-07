#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試最大的Whisper模型

這個腳本會下載並使用OpenAI的Whisper large-v3模型進行語音轉文字。
它會顯示可用的GPU設備，並使用GPU進行處理（如果可用）。
完成轉錄後會刪除原始音頻文件。

可以直接提供音頻文件路徑，或者提供YouTube影片ID來處理voices資料夾中的音頻。
也可以使用 --all 參數處理 voices 資料夾內的所有音訊檔案。
使用 --background 參數可以在背景執行程式，並將輸出記錄到日誌檔案中。
"""

import os
import sys
import torch
import whisper
from datetime import datetime
import glob
import argparse
import logging
import time
import subprocess

def setup_logging(log_file=None):
    """設置日誌記錄"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if log_file:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format
        )

def process_audio_file(model, audio_path, delete_after=True):
    """處理單個音頻文件"""
    if os.path.exists(audio_path):
        logging.info(f"\n=== 開始轉錄音頻: {audio_path} ===")
        start_time = datetime.now()
        logging.info(f"開始時間: {start_time}")
        
        # 使用模型進行轉錄
        result = model.transcribe(audio_path)
        
        end_time = datetime.now()
        logging.info(f"結束時間: {end_time}")
        logging.info(f"轉錄耗時: {end_time - start_time}")
        
        # 輸出轉錄結果
        logging.info("\n=== 轉錄結果 ===")
        logging.info(result["text"])
        
        # 保存轉錄結果到文件
        # 如果音頻文件在voices資料夾中，則將結果保存到原始影片ID的資料夾
        if '/voices/' in audio_path:
            # 從路徑中提取影片ID
            parts = audio_path.split('/voices/')
            if len(parts) > 1:
                video_id_path = parts[1].split('/', 1)[0]
                # 確保原始影片ID資料夾存在
                video_dir = os.path.join(os.path.dirname(os.path.dirname(audio_path)), video_id_path)
                os.makedirs(video_dir, exist_ok=True)
                output_file = os.path.join(video_dir, f"{os.path.splitext(os.path.basename(audio_path))[0]}_transcript.txt")
            else:
                output_file = f"{os.path.splitext(audio_path)[0]}_transcript.txt"
        else:
            output_file = f"{os.path.splitext(audio_path)[0]}_transcript.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
        logging.info(f"\n轉錄結果已保存到: {output_file}")
        
        # 刪除原始音頻文件
        if delete_after:
            try:
                os.remove(audio_path)
                logging.info(f"已刪除原始音頻文件: {audio_path}")
            except Exception as e:
                logging.error(f"刪除原始音頻文件時出錯: {e}")
        
        return True
    else:
        logging.error(f"錯誤: 找不到音頻文件 '{audio_path}'")
        return False

def process_all_audio_files(model, base_dir='voices', delete_after=True):
    """處理指定目錄下的所有音頻文件，包括子目錄"""
    if not os.path.exists(base_dir):
        logging.error(f"錯誤: 找不到目錄 '{base_dir}'")
        return False
    
    logging.info(f"\n=== 開始處理 {base_dir} 目錄下的所有音頻文件 ===")
    
    # 獲取所有音頻文件
    audio_extensions = ('.mp3', '.wav', '.m4a', '.mp4', '.webm')
    audio_files = []
    
    # 遍歷目錄及其子目錄
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        logging.error(f"在 {base_dir} 及其子目錄中找不到任何音頻文件")
        return False
    
    logging.info(f"找到 {len(audio_files)} 個音頻文件")
    
    # 處理每個音頻文件
    successful = 0
    for i, audio_file in enumerate(audio_files):
        logging.info(f"\n處理第 {i+1}/{len(audio_files)} 個文件")
        if process_audio_file(model, audio_file, delete_after):
            successful += 1
    
    logging.info(f"\n=== 處理完成 ===")
    logging.info(f"成功處理 {successful}/{len(audio_files)} 個音頻文件")
    
    return True

def run_in_background(args):
    """在背景執行程式"""
    # 創建日誌目錄
    os.makedirs('logs', exist_ok=True)
    
    # 生成日誌檔案名稱
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/whisper_transcribe_{timestamp}.log"
    
    # 構建命令
    cmd = [sys.executable, __file__]
    
    # 添加參數，但排除 --background
    if args.input:
        cmd.append(args.input)
    if args.all:
        cmd.append('--all')
    if args.keep:
        cmd.append('--keep')
    
    # 添加日誌檔案參數
    cmd.append('--log')
    cmd.append(log_file)
    
    # 在背景執行
    with open(os.devnull, 'w') as devnull:
        process = subprocess.Popen(
            cmd,
            stdout=devnull,
            stderr=devnull,
            close_fds=True
        )
    
    print(f"程式已在背景啟動，進程ID: {process.pid}")
    print(f"輸出將記錄到: {log_file}")
    print(f"您可以使用以下命令查看日誌:")
    print(f"  tail -f {log_file}")
    
    return process.pid

def main():
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='使用Whisper large-v3模型進行語音轉文字')
    parser.add_argument('input', nargs='?', help='音頻文件路徑或YouTube影片ID')
    parser.add_argument('--all', action='store_true', help='處理voices資料夾內的所有音訊檔案')
    parser.add_argument('--keep', action='store_true', help='保留原始音頻文件（不刪除）')
    parser.add_argument('--background', action='store_true', help='在背景執行程式')
    parser.add_argument('--log', help='指定日誌檔案路徑')
    args = parser.parse_args()
    
    # 如果指定了在背景執行
    if args.background:
        run_in_background(args)
        return
    
    # 設置日誌記錄
    setup_logging(args.log)
    
    # 檢查GPU是否可用
    logging.info(f"=== GPU 可用性 ===")
    logging.info(f"CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logging.info(f"CUDA 設備數量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            logging.info(f"設備 {i}: {torch.cuda.get_device_name(i)}")
        logging.info(f"當前設備: {torch.cuda.current_device()}")
    
    # 設置CUDA設備（如果有多個GPU，可以選擇使用哪一個）
    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        # 使用第一個GPU
        torch.cuda.set_device(0)
        logging.info(f"已設置為使用設備 {torch.cuda.current_device()}: {torch.cuda.get_device_name()}")
    
    # 載入最大的Whisper模型
    logging.info("\n=== 開始載入 Whisper large-v3 模型 ===")
    start_time = datetime.now()
    logging.info(f"開始時間: {start_time}")
    
    # 載入large-v3模型（這會自動下載模型，如果尚未下載）
    model = whisper.load_model("large-v3")
    
    end_time = datetime.now()
    logging.info(f"結束時間: {end_time}")
    logging.info(f"載入模型耗時: {end_time - start_time}")
    
    # 顯示模型信息
    logging.info(f"\n=== 模型信息 ===")
    logging.info(f"模型類型: {type(model)}")
    logging.info(f"模型名稱: large-v3")
    
    # 處理命令行參數
    if args.all:
        # 處理voices資料夾內的所有音訊檔案
        process_all_audio_files(model, 'voices', not args.keep)
    elif args.input:
        # 檢查是否是直接提供的音頻文件路徑
        if os.path.exists(args.input):
            process_audio_file(model, args.input, not args.keep)
        # 檢查是否是YouTube影片ID
        elif len(args.input) == 11 and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.input):
            # 在voices資料夾中尋找對應的音頻文件
            voices_dir = os.path.join('voices', args.input)
            if os.path.exists(voices_dir):
                audio_files = glob.glob(os.path.join(voices_dir, '*.*'))
                if audio_files:
                    for audio_file in audio_files:
                        # 只處理音頻文件
                        if audio_file.lower().endswith(('.mp3', '.wav', '.m4a', '.mp4', '.webm')):
                            process_audio_file(model, audio_file, not args.keep)
                else:
                    logging.error(f"在 {voices_dir} 中找不到任何音頻文件")
            else:
                logging.error(f"找不到影片ID為 {args.input} 的資料夾")
        else:
            logging.error(f"無效的參數: {args.input}")
    else:
        logging.info("\n使用方法:")
        logging.info("1. 提供音頻文件路徑: python test_whisper_large.py <音頻文件路徑>")
        logging.info("2. 提供YouTube影片ID: python test_whisper_large.py <影片ID>")
        logging.info("3. 處理所有音頻文件: python test_whisper_large.py --all")
        logging.info("4. 保留原始音頻文件: 添加 --keep 參數")
        logging.info("5. 在背景執行: 添加 --background 參數")

if __name__ == "__main__":
    main() 