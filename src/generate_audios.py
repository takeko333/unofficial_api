import os
import io
import re
import sys
import shutil
import requests
import pathlib
import textwrap

from tqdm import tqdm
from glob import glob
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment

def text_to_wav(text, speaker, speed=1.0, pitch=0.0, timeout=15, url="http://localhost:50021/", buffer_duration=500):
    params = {"text": text, "speaker": speaker}
    query_synthesis_response = requests.post(url + "audio_query", params=params, timeout=timeout)
    query_synthesis_json = query_synthesis_response.json()
    query_synthesis_json["speedScale"] = speed
    query_synthesis_json["pitchScale"] = pitch
    synthesis_response = requests.post(url + "synthesis", params=params, json=query_synthesis_json)
    audio_segment = AudioSegment.from_file(io.BytesIO(synthesis_response.content), format="wav")
    silent_buffer = AudioSegment.silent(duration=buffer_duration, frame_rate=audio_segment.frame_rate)    
    return audio_segment + silent_buffer

def cleaning_text(text):
    text = re.sub("[「・」]", "", text)
    text = re.sub("、", ",", text)
    text = re.sub("。", ".", text)
    return text

if __name__ == "__main__":

    speaker = 13    
    desired_speed = 1.15  # 通常より速くする
    desired_pitch = -0.05  # 少し音を高くする

    load_dir = f"data/reddit/subreddit/{sys.argv[1]}/results/checked/"
    load_path_list = glob(load_dir + "*.txt")

    for load_path in load_path_list:
        with open(load_path, "r", encoding="shift-jis") as f:
            lines = [line.replace("\n", "") for line in f.readlines() if line != "\n"]
        filename = os.path.basename(load_path)
        basename = filename.split(".")[0]
        save_dir = load_dir + basename
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        idx = 0
        for line in tqdm(lines):
            wav_save_path = f"{save_dir}/{idx}.wav"
            wav = text_to_wav(cleaning_text(line), speaker, speed=desired_speed, pitch=desired_pitch)
            wav.export(wav_save_path, format="wav")
            idx += 1
        new_path = shutil.move(load_path, f"{save_dir}/{basename}_edited.txt")
        new_path = shutil.move(load_dir.replace("checked/", "") + filename, f"{save_dir}/{filename}")