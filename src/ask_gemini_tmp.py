import os
import sys
import time
import requests
import pyperclip
import mimetypes
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime

# グローバル変数の初期化
page = None

def connect_and_ask(base_dir):
    global page
    with sync_playwright() as p:
        try:
            print("実行中のChromeに接続しています...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("接続に成功しました。")
            input_text = "犬の画像を生成してください"
            save_dir = os.path.join(base_dir, "results")
            success = run_gemini_image_task(page, input_text, save_dir)
        except Exception as e:
            print(f"エラー発生: {e}")

def run_gemini_image_task(target_page, input_text, save_dir):
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
            target_page.wait_for_selector(img_selector, timeout=90000)
        except:
            print("画像が見つかりませんでした。")
            return False
            
        time.sleep(3) # 描画安定待ち

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        images = target_page.query_selector_all(img_selector)
        
        for i, img_handle in enumerate(images):
            src = img_handle.get_attribute("src")
            if not src: continue

            # --- 💡 新しいアプローチ: 新規タブで画像を開いて保存 ---
            try:
                # 1. 画像のURLを新しいコンテキスト（タブ）で直接開く
                # これにより、ブラウザの「画像表示機能」としてアクセスするためブロックされません
                new_page = target_page.context.new_page()
                response = new_page.goto(src)
                
                if response and response.status == 200:
                    # 2. ページのボディ（画像データそのもの）を取得
                    buffer = response.body()
                    
                    # 3. Content-Typeから拡張子を特定
                    content_type = response.headers.get("content-type", "")
                    ext = ".webp" if "webp" in content_type else ".png"
                    
                    dateinfo = datetime.now().strftime("%Y%m%d%H%M%S")
                    filepath = os.path.join(save_dir, f"{dateinfo}_{i}{ext}")
                    
                    with open(filepath, "wb") as f:
                        f.write(buffer)
                    print(f"保存成功: {filepath} ({content_type})")
                
                new_page.close() # タブを閉じる
                
            except Exception as inner_e:
                print(f"画像 {i} の取得に失敗: {inner_e}")
                if 'new_page' in locals(): new_page.close()

        return True

    except Exception as e:
        print(f"全体エラー: {e}")
        return False

if __name__ == '__main__':

    base_dir = ""
    connect_and_ask(base_dir)