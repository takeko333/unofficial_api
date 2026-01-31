import os
import re
import sys
import time
import requests
import pyperclip
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from extract_contents import get_text, get_comments

# グローバル変数の初期化
page = None

def connect_and_ask(base_dir, target=""):
    global page
    with sync_playwright() as p:
        try:
            print("実行中のChromeに接続しています...")
            # 事前に Chrome を --remote-debugging-port=9222 で起動しておく必要があります
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("接続に成功しました。")

            with open(base_dir + "prompt.txt", "r", encoding='utf-8') as f:
                prompt = "".join(f.readlines())
            with open(base_dir + "urls.txt", "r") as f:
                urls = [line[:-1] for line in f.readlines()]
                urls = [url if url[-1] == "/" else url + "/" for url in urls]
            used_urls = []
            for url in urls:
                print(url)
                if target == "comments":
                    comments = get_comments(url + ".json")
                    for i, comment in enumerate(comments):
                        input_text = prompt + "\n" + "\n".join(comment)
                        output_text = run_gemini_task(page, input_text)
                        if output_text:
                            save_path = get_save_path(url, base_dir, f" ({i})")
                            with open(save_path, "w", errors='replace') as f:
                                f.write(output_text)
                            if url not in used_urls:
                                used_urls.append(url)
                        else:
                            raise ValueError("タイムアウトしました。")
                else:
                    text = get_text(url)
                    input_text = prompt + "\n" + text
                    output_text = run_gemini_task(page, input_text)
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

def run_gemini_task(target_page, input_text):
    try:
        target_page.goto("https://gemini.google.com/app?hl=ja")
        input_selector = 'div[contenteditable="true"]'
        target_page.wait_for_selector(input_selector, timeout=10000)
        target_page.focus(input_selector)
        target_page.click(input_selector)
        # 既存テキスト削除
        target_page.keyboard.press("Control+A")
        target_page.keyboard.press("Backspace")
        # テキストを入力
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

def get_save_path(url, base_dir, no=""):
    output_dir = base_dir + "results"
    dateinfo = datetime.now().strftime("%Y%m%d%H%M%S")
    values = url.split("/")
    community_name = values[-1]
    title = values[-2].replace("_", " ").title().replace(" ", "")
    title = re.sub(r'[<>:"/\\|?*#]', '_', title)
    save_path = f"{output_dir}/{dateinfo}_{community_name}_{title}{no}.txt"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    return save_path

def evacuate_urls(urls, used_urls, base_dir):
    unused_urls = [url for url in urls if url not in used_urls]
    with open(base_dir + "urls.txt", "w") as f:
        for url in unused_urls:
            f.write(url + "\n")
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

    targets = {
        "AskReddit": "comments",
        "CreepyWikipedia": "", 
        "nosleep": "",
        "Paranormal": "",
    }

    if sys.argv[1] == "reddit" and sys.argv[2] is not None:
        base_dir = f"data/reddit/subreddit/{sys.argv[2]}/"
        target = targets[sys.argv[2]]
        connect_and_ask(base_dir, target=target)