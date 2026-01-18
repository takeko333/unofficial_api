import time
import threading
from playwright.sync_api import sync_playwright
from flask import Flask, render_template, request

app = Flask(__name__)

def connect_to_existing_chrome():
    # Flaskが起動するまで少し待つ
    time.sleep(3)
    
    # playwrightの接続（withを使わずstartで制御するか、操作が終わるまで抜けないようにする）
    with sync_playwright() as p:
        try:
            print("実行中のChromeに接続しています...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # 既存のコンテキストまたは新規作成
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            
            # 1つ目のタブでFlaskアプリを開く
            page0 = context.pages[0] if context.pages else context.new_page()
            page0.goto("http://127.0.0.1:5000")
            
            # 2つ目のタブでGeminiを開く
            page1 = context.new_page()
            page1.goto("https://gemini.google.com/app?hl=ja")
            
            print("接続・遷移に成功しました。")
            # 遷移を安定させるために少し待機
            time.sleep(3)
            
        except Exception as e:
            print(f"Playwrightエラー: {e}")

@app.route('/')
def index():
    return render_template('index.html', title="Flaskデモサイト", message="名前を入力して送信してください。")

# ... greet関数などは変更なし ...

if __name__ == '__main__':
    # Flaskを別スレッドで動かすか、Flask起動後にブラウザ操作を行う必要があります。
    # 最も簡単な方法は、別スレッドでPlaywrightを実行することです。
    threading.Thread(target=connect_to_existing_chrome, daemon=True).start()
    
    # debug=Trueだと2回実行されてしまうため、Falseにするか、
    # use_reloader=Falseを設定します。
    app.run(debug=True, use_reloader=False)