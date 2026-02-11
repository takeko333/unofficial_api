import os
import re
import asyncio
import sys
from datetime import timedelta
from moviepy.editor import VideoFileClip, concatenate_videoclips
from googletrans import Translator

# Windows特有のエラー対策
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def concatenate_mp4_files(input_folder, output_filename, insert_clip_path="data/insert.mp4", start_time=3.0):
    video_files = [f for f in os.listdir(input_folder) if f.endswith('.mp4')]
    video_files.sort()
    
    if output_filename in video_files:
        video_files.remove(output_filename)
    if not video_files:
        print("連結するmp4ファイルが見つかりませんでした。")
        return

    clips = []
    current_time = start_time
    timestamps = []

    try:
        # async with で translator を確実に終了させる
        async with Translator() as translator:
            for i, file in enumerate(video_files):
                file_path = os.path.join(input_folder, file)
                clip = VideoFileClip(file_path)
                
                title_raw = file.split("_")[-1].replace(".mp4", "")
                title_spaced = re.sub(r'([A-Z])', r' \1', title_raw).strip()
                
                # 翻訳
                # translated_res = await translator.translate(title_spaced, src='en', dest='ja')
                
                timestamps.append({
                    "start_at": str(timedelta(seconds=int(current_time))),
                    "idx": str(i+1).zfill(2), 
                    # "title": translated_res.text, 
                })
                
                clips.append(clip)
                current_time += clip.duration
                
                if i < len(video_files) - 1:
                    insert_clip = VideoFileClip(insert_clip_path)
                    clips.append(insert_clip)
                    current_time += insert_clip.duration

        # テキスト保存
        with open("timestamps.txt", "w", encoding="utf-8") as f:
            for ts in timestamps:
                f.write(f"{ts['start_at']}　{ts['idx']}話目\n")

        # 動画連結
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")        
        print(f"成功！保存先: {output_filename}")

    finally:
        for clip in clips:
            clip.close()

if __name__ == "__main__":
    input_folder = "projects/now/outputs/videos"
    asyncio.run(concatenate_mp4_files(input_folder, "tmp.mp4"))