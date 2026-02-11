import os
import re
import sys
import time
import requests
import pyperclip
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from glob import glob
from extract_contents import get_text, get_comments

# グローバル変数の初期化
page = None

def generate_text_with_gemini(base_dir):
    global page
    with sync_playwright() as p:
        urls = []
        tags = []
        used_urls = []
        try:
            print("実行中のChromeに接続しています...")
            # 事前に Chrome を --remote-debugging-port=9222 で起動しておく必要があります
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("接続に成功しました。")
            with open(base_dir + "prompts/generate_text_from_post.txt", "r", encoding='utf-8') as f:
                generate_text_from_post_prompt = "".join(f.readlines())
            with open(base_dir + "prompts/generate_text_from_comments.txt", "r", encoding='utf-8') as f:
                generate_text_from_comments_prompt = "".join(f.readlines())
            with open(base_dir + "urls.txt", "r") as f:
                lines = f.readlines()
            for line in lines:
                url, tag = line[:-1].split(", ")
                if "AskReddit" in url:
                    tag = "Question"
                url = url if url[-1] == "/" else url + "/"
                urls.append(url)
                tags.append(tag)
            for url, tag in zip(urls, tags):
                print(url)
                if tag == "Question":
                    output_texts = []
                    comments = get_comments(url + ".json")
                    for i, comment in enumerate(comments):
                        input_text = generate_text_from_comments_prompt + "\n" + "\n".join(comment)
                        output_text = get_generated_text(page, input_text)
                        if output_text:
                            output_texts.append(output_text)
                    save_path = get_save_path(url, base_dir)
                    with open(save_path, "w", errors='replace') as f:
                        f.write(f"{'-' * 25}\n".join(output_texts))
                    if url not in used_urls:
                        used_urls.append(url)
                else:
                    text = get_text(url)
                    input_text = generate_text_from_post_prompt + "\n" + text
                    output_text = get_generated_text(page, input_text)
                    if output_text:
                        save_path = get_save_path(url, base_dir)
                        with open(save_path, "w", errors='replace') as f:
                            f.write(output_text)
                        used_urls.append(url)
                    else:
                        raise ValueError("タイムアウトしました。")
        except Exception as e:
            print(f"Playwrightエラー: {e}")
        finally:
            evacuate_urls(urls, used_urls, base_dir)

def get_generated_text(target_page, input_text):
    try:
        target_page.goto("https://gemini.google.com/app?hl=ja")
        input_selector = 'div[contenteditable="true"]'
        target_page.wait_for_selector(input_selector, timeout=10000)
        target_page.focus(input_selector)
        target_page.click(input_selector)
        target_page.keyboard.press("Control+A")
        target_page.keyboard.press("Backspace")
        pyperclip.copy(input_text)
        target_page.keyboard.press("Control+V")
        time.sleep(0.5)
        target_page.keyboard.press("Enter")
        print("回答を待機中...")
        last_text = ""
        stable_count = 0
        for _ in range(60):
            time.sleep(1)
            elements = target_page.query_selector_all('.model-response-text, .message-content, model-response')
            if elements:
                current_text = elements[-1].inner_text()
                if current_text == last_text and len(current_text) > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                last_text = current_text
                if stable_count >= 5:
                    return last_text
        return None
    except Exception as e:
        return f"操作失敗: {e}"

def generate_image_with_gemini(base_dir):
    global page
    with sync_playwright() as p:
        try:
            print("実行中のChromeに接続しています...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("接続に成功しました。")
            with open(base_dir + "prompts/generate_image_ideas.txt", "r", encoding='utf-8') as f:
                generate_image_ideas_prompt = "".join(f.readlines())
            with open(base_dir + "prompts/generate_image.txt", "r", encoding='utf-8') as f:
                generate_image_prompt = "".join(f.readlines())
            path_list = glob(base_dir + "results/checked/*.txt")
            for path in path_list:
                basename = os.path.basename(path).split(".")[0]
                save_dir = base_dir + f"results/checked/{basename}"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                with open(path, "r") as f:
                    text = "".join(f.readlines())
                input_text = generate_image_ideas_prompt + "\n" + text
                while True:
                    output_text = get_generated_text(page, input_text)
                    lines = [s.strip() for s in re.split(r'\d+行目,', output_text) if s.strip()]
                    if len(lines) != 1:
                        break
                    lines = [s.strip() for s in re.split(r'\d+,', output_text) if s.strip()]
                    if len(lines) != 1:
                        break
                for idx, line in enumerate(lines):
                    print(line)
                    input_text = generate_image_prompt + "\n" + line
                    save_generated_image(page, input_text, save_dir, idx)
        except Exception as e:
            print(f"エラー発生: {e}")

def save_generated_image(target_page, input_text, save_dir, idx):
    try:
        target_page.goto("https://gemini.google.com/app?hl=ja")
        input_selector = 'div[contenteditable="true"]'
        target_page.wait_for_selector(input_selector, timeout=10000)
        target_page.click(input_selector)
        pyperclip.copy(input_text)
        target_page.keyboard.press("Control+V")
        time.sleep(0.5)
        target_page.keyboard.press("Enter")
        print("画像生成を待機中...")
        img_selector = 'model-response img[src*="googleusercontent"]'        
        try:
            target_page.wait_for_selector(img_selector, timeout=500000)
        except:
            print("画像が見つかりませんでした。")
            return False
        time.sleep(3) # 描画安定待ち
        images = target_page.query_selector_all(img_selector)
        for i, img_handle in enumerate(images):
            src = img_handle.get_attribute("src")
            if not src: continue
            try:
                new_page = target_page.context.new_page()
                response = new_page.goto(src)
                if response and response.status == 200:
                    buffer = response.body()
                    content_type = response.headers.get("content-type", "")
                    ext = ".webp" if "webp" in content_type else ".png"
                    filepath = os.path.join(save_dir, f"{idx}{ext}")
                    with open(filepath, "wb") as f:
                        f.write(buffer)
                    print(f"保存成功: {filepath} ({content_type})")
                new_page.close()
            except Exception as inner_e:
                print(f"画像 {i} の取得に失敗: {inner_e}")
                if 'new_page' in locals(): 
                    new_page.close()
    except Exception as e:
        print(f"エラー発生: {e}")

def get_save_path(url, base_dir, no=""):
    output_dir = base_dir + "results"
    dateinfo = datetime.now().strftime("%Y%m%d%H%M%S")
    values = url.split("/")
    community_name = values[-5]
    title = values[-2].replace("_", " ").title().replace(" ", "")
    title = re.sub(r'[<>:"/\\|?*#]', '_', title)
    save_path = f"{output_dir}/{dateinfo}_{community_name}_{title}{no}.txt"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    return save_path

def evacuate_urls(urls, used_urls, base_dir):
    if urls:
        unused = []
        for url in urls:
            if url not in used_urls:
                unused.append(f"{url}, {tag}\n")
        with open(base_dir + "urls.txt", "w") as f:
            for value in unused:
                f.write(value)
        save_path = base_dir + "used_urls.txt"
        if not os.path.isfile(save_path):
            with open(save_path, "w") as f:
                pass
        with open(save_path, "r") as f:
            past_used_urls = [line[:-1] for line in f.readlines()]
        with open(save_path, "a") as f:
            for url in used_urls:
                if url not in past_used_urls:
                    f.write(url + "\n")

if __name__ == '__main__':

    if len(sys.argv) == 3:
        base_dir = f"data/reddit/subreddit/{sys.argv[1]}/"
        if sys.argv[2] == "text":
            generate_text_with_gemini(base_dir)
        if sys.argv[2] == "image":
            generate_image_with_gemini(base_dir)
    else:
        print("標準入力が不正です。")