import os
import glob
from mutagen.mp3 import MP3
import re
from datetime import timedelta

def create_mp3_timestamps(folder_path):
    """
    指定されたフォルダ内のMP3ファイルの再生時間を取得し、タイムスタンプを作成する関数
    
    Args:
        folder_path (str): MP3ファイルが格納されているフォルダのパス
    """
    
    # 指定されたフォルダ内のすべてのMP3ファイルを取得
    mp3_files = glob.glob(os.path.join(folder_path, '*.mp3'))
    sorted_files = sorted(mp3_files)
    
    total_duration_sec = 0
    timestamps = []
    
    print(f"フォルダ '{folder_path}' のMP3ファイルからタイムスタンプを作成します...")

    i = 1
    for file_path in sorted_files:
        try:
            # MP3ファイルの再生時間を取得
            audio = MP3(file_path)
            duration_sec = audio.info.length
            
            # 累積再生時間からタイムスタンプを作成
            timestamp = str(timedelta(seconds=int(total_duration_sec)))
            
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            
            # タイムスタンプの文字列を作成してリストに追加
            timestamps.append(f"{str(i).zfill(2)}曲目 {timestamp}")
            print(f"{timestamps[-1]} {file_name}")
            
            # 累積再生時間を更新
            total_duration_sec += duration_sec
            i += 1
            
        except Exception as e:
            print(f"エラー: '{file_path}' の処理中に問題が発生しました - {e}")
            
    # 結果の表示
    if timestamps:
        with open("timestamp.txt", "w") as f:
            f.write("タイムスタンプは↓に記載\n")
            for ts in timestamps:
                f.write(ts + "\n")
    else:
        print("\n指定されたフォルダにMP3ファイルが見つかりませんでした。")

# --- 実行部分 ---
if __name__ == "__main__":
    # 対象フォルダのパスを指定
    target_folder = "mp3" # 例：特定のフォルダを指定する場合
    
    create_mp3_timestamps(target_folder)