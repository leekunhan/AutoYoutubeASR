#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目的：示範使用 OpenAI Whisper 進行語音轉文字的簡易程式。

用法：
  1. 先執行 setup_whisper.sh 安裝好環境與 Whisper。
  2. 在同個 Shell (並啟動 whisper_env) 下執行：
       python transcribe.py <音訊檔案路徑>
  例如：
       python transcribe.py example.mp3
"""

import sys
import whisper

def main():
    if len(sys.argv) < 2:
        print("用法：python transcribe.py <音訊檔案路徑>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # 載入模型 (可以改成 "tiny", "base", "medium", "large" 等)
    print("=== 載入 Whisper 模型：small ===")
    model = whisper.load_model("small")

    print(f"=== 處理音訊檔：{audio_path} ===")
    result = model.transcribe(audio_path)
    
    print("=== 轉錄結果如下 ===")
    print(result["text"])


if __name__ == "__main__":
    main()
