#!/bin/bash
#
# 目的：在 Linux 環境上自動安裝 Python、ffmpeg 及 Whisper。
# 用法：
#   1. 先設定本檔執行權限：chmod +x setup_whisper.sh
#   2. 執行：./setup_whisper.sh
#
# 注意：以下以 Ubuntu/Debian 為例，如果您使用其他 Linux 發行版，
#       請自行調整套件管理工具 (e.g., yum, dnf, pacman, zypper 等)。

echo "=== STEP 1: 系統更新與安裝必要套件 ==="
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip ffmpeg

echo "=== STEP 2: 建立與啟動 Python 虛擬環境 ==="
python3 -m venv whisper_env

# 若要在同一個 Shell 中啟動 venv，需要用 source
# 若是在 script 內執行，結束後會回到外層環境；若您需要常駐可以手動 source
source whisper_env/bin/activate

echo "=== STEP 3: 升級 pip 與安裝 Whisper ==="
pip install --upgrade pip
pip install git+https://github.com/openai/whisper.git

echo "=== 完成！=== "
echo "您現在已經在 whisper_env 虛擬環境中，可以直接使用 'whisper --help' 測試。"
echo "離開虛擬環境請輸入 'deactivate'。"
