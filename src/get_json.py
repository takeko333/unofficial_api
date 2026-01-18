import json
import requests
import time

def get_reddit_posts(subreddit, max_pages=3):
    posts_all = []
    after = None
    headers = {"User-Agent": "MyRedditScraper/1.0"}

    for i in range(max_pages):
        # afterパラメータをURLに付与して次のページを指定
        url = f"https://www.reddit.com/r/{subreddit}/.json?limit=100"
        if after:
            url += f"&after={after}"
        
        print(f"{i+1}ページ目を取得中: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 投稿リストを抽出して結合
            current_posts = data['data']['children']
            posts_all.extend(current_posts)
            
            # 次のページの識別子（after）を更新
            after = data['data']['after']
            
            # afterがNone（これ以上投稿がない）なら終了
            if not after:
                break
                
            # Redditのサーバーに負荷をかけないよう少し待機（マナー）
            time.sleep(1)
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            break

    # 結果を保存
    with open("reddit_data.json", "w", encoding="utf-8") as f:
        json.dump(posts_all, f, indent=4, ensure_ascii=False)
    
    print(f"合計 {len(posts_all)} 件の投稿を保存しました。")

if __name__ == "__main__":
    
    get_reddit_posts("nosleep", max_pages=5) # 5ページ分（最大500件）取得を試みる