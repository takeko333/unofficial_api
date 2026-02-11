import os
import io
import re
import glob
import requests
import pathlib
import textwrap
import subprocess

from tqdm import tqdm
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, concatenate_audioclips

def text_to_audio(text, speaker, speed=1.0, pitch=0.0, timeout=15, url="http://localhost:50021/", buffer_duration=500):
    params = {"text": text, "speaker": speaker}
    query_synthesis_response = requests.post(url + "audio_query", params=params, timeout=timeout)
    query_synthesis_json = query_synthesis_response.json()
    query_synthesis_json["speedScale"] = speed
    query_synthesis_json["pitchScale"] = pitch
    synthesis_response = requests.post(url + "synthesis", params=params, json=query_synthesis_json)
    audio_segment = AudioSegment.from_file(io.BytesIO(synthesis_response.content), format="wav")
    silent_buffer = AudioSegment.silent(duration=buffer_duration, frame_rate=audio_segment.frame_rate)    
    return audio_segment + silent_buffer

def text_to_image(text, font_path, font_size=40, image_size=(1280, 720), background=None):
    image = Image.new("RGBA", image_size, (255, 255, 255, 0))
    if background is not None:
        image.paste(background)
    
    width, height = image.size
    draw = ImageDraw.Draw(image)
    
    try:
        # Windowsのパス指定は raw文字列(r"") にするかスラッシュを使うのが安全です
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print("フォントが見つかりません。")
        return

    # 1. テキストの整形（折り返し処理）
    lines = []
    max_text_width = width * 0.8
    wrapp_width = int(max_text_width // font_size)    
    for paragraph in text.split("\n"):
        if paragraph != "":
            # 1行が長すぎる場合は折り返し
            if draw.textlength(paragraph, font=font) > max_text_width:
                lines.extend(textwrap.wrap(paragraph, width=wrapp_width))
            else:
                lines.append(paragraph)
    
    full_text = "\n".join(lines)

    # 2. テキスト全体の範囲（バウンディングボックス）を計算
    # これにより、複数行のテキストが占める「塊」のサイズがわかります
    bbox = draw.multiline_textbbox((0, 0), full_text, font=font, stroke_width=3.5)
    block_w = bbox[2] - bbox[0]
    block_h = bbox[3] - bbox[1]

    # 3. 画像の中心に「塊」が来るように左上の座標(x, y)を計算
    x = (width - block_w) / 2
    y = (height - block_h) / 2

    # 4. 描画
    # align="left" にすることで、塊の中では左揃えになります
    draw.multiline_text(
        (x, y), 
        full_text, 
        font=font, 
        fill=(255, 255, 255, 255), 
        stroke_width=5, 
        stroke_fill=(0, 0, 0, 100),
        align="left", 
        spacing=10
    )

    return image

def concat_audios(audio_paths, output_path):
    with open("projects/now/outputs/audio_list.txt", "w") as f:
        for audio_path in audio_paths:
            x = os.path.abspath(audio_path).replace("\\", "/")
            f.write(f"file '{x}'\n")
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "projects/now/outputs/audio_list.txt",
        "-c", "copy",
        output_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("FFmpegによる音声連結が完了しました。")
    except subprocess.CalledProcessError as e:
        print(f"FFmpegエラー: {e}")

def concat_images(image_paths, audio_paths, output_path, fps=24, fade_duration=0.01):
    video_clips = []
    for image_path, audio_path in tqdm(zip(image_paths, audio_paths)):
        try:
            audio_clip_segment = AudioFileClip(audio_path)
            image_clip_segment = ImageClip(image_path).set_duration(audio_clip_segment.duration)
            video_clips.append(image_clip_segment)            
        except Exception as e:
            print(f"ファイル処理中にエラーが発生しました ({image_path}, {audio_path}): {e}")
            continue
    if not video_clips:
        print("エラー: 有効なクリップが作成されませんでした。")
        return
    final_video_clip = concatenate_videoclips(video_clips)
    try:
        final_video_clip.write_videofile(
            output_path, 
            fps=fps, 
            codec="libx264", 
            audio_codec="pcm_s16le" # 非圧縮PCMを使用
        )
        print("動画の生成が完了しました！")
    except Exception as e:
        print(f"動画生成中にエラーが発生しました: {e}")

def add_static_audio_to_video(audio_path, image_path, output_path):
    audio = AudioFileClip(audio_path)
    video = VideoFileClip(image_path).set_duration(audio.duration)    
    final_clip = video.set_audio(audio)
    final_clip = final_clip.subclip(0, audio.duration)    
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

def insert_newline(text):
    brackets = {'(': ')', '（': '）', '「': '」', '『': '』', '[': ']', '{': '}', '〈': '〉', '《': '》'}
    stack = []
    result = ''
    i = 0
    while i < len(text):
        char = text[i]
        if char in brackets:
            # 括弧の開始。対応する終了括弧が見つかるまでスキップ。
            start = i
            end_char = brackets[char]
            depth = 1
            i += 1
            while i < len(text) and depth > 0:
                if text[i] == char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                i += 1
            result += text[start:i]
        elif char == '。':
            result += '。\n'
            i += 1
        else:
            result += char
            i += 1
    return result

def cleaning_text(text):
    text = re.sub("[「・」]", "", text)
    text = re.sub("、", ",", text)
    text = re.sub("。", ".", text)
    return text

if __name__ == "__main__":

    base_dir = "projects/now"
    paths = sorted(glob.glob(f"{base_dir}/inputs/*.txt"))

    desired_speed = 1
    desired_pitch = 0
    speaker_id = 14

    font_path = "C:\Windows\Fonts\meiryo.ttc"
    image_size=(1280, 720)
    background = Image.open(f"{base_dir}/inputs/bg.png")

    for path in paths:
        print(path)
        with open(path, "r", encoding="shift_jis") as f:
            lines = [line.replace("\n", "") for line in f.readlines() if line != "\n"]
        idx = 1
        filename = os.path.basename(path)
        basename = filename.split(".")[0]

        audio_save_dir = f"{base_dir}/outputs/audios/{basename}/"
        if not os.path.exists(audio_save_dir):
            os.makedirs(audio_save_dir)

        image_save_dir = f"{base_dir}/outputs/images/{basename}/"
        if not os.path.exists(image_save_dir):
            os.makedirs(image_save_dir)

        audio_paths = []
        image_paths = []
        for line in tqdm(lines):
            audio_save_path = audio_save_dir + str(idx).zfill(3) + ".wav"
            audio = text_to_audio(cleaning_text(line), speaker_id, speed=desired_speed, pitch=desired_pitch)
            audio.export(audio_save_path, format="wav")
            audio_paths.append(audio_save_path)
            image_save_path = image_save_dir + str(idx).zfill(3) + ".png"
            image = text_to_image(line, font_path, image_size=image_size, background=background)
            image.save(image_save_path)
            image_paths.append(image_save_path)
            idx += 1

        concat_audio_path = f"{base_dir}/outputs/audios/{basename}.wav"
        concat_image_path = f"{base_dir}/outputs/images/{basename}.mp4"

        final_product_dir = f"{base_dir}/outputs/videos/"
        if not os.path.exists(final_product_dir):
            os.makedirs(final_product_dir)
        final_product_path = final_product_dir + f"{basename}.mp4"

        concat_audios(audio_paths, concat_audio_path)
        concat_images(image_paths, audio_paths, concat_image_path)

        add_static_audio_to_video(concat_audio_path, concat_image_path, final_product_path)