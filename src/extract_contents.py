import json
import requests
import wikipedia
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
wikipedia.set_lang("en")

def get_text(url):
    try:
        if "wikipedia.org" in url:
            title = url.split("/")[-2]
            title = title.split("#")[0]
            title = title.split("?")[0]
            title = title.replace("_", " ")
            print(title)
            data = wikipedia.page(title)
            return data.content
        else:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text(strip=True, separator='\n')
    except Exception as e:
        return f"エラー: {e}"

def get_comments(url):
    url += ".json"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        comments = group_comments_by_parent(data)
        return comments
    except Exception as e:
        return f"エラー: {e}"

def extract_all_bodies_recursive(data, results):
    """
    特定のコメントツリー（枝）からすべてのbodyを再帰的に回収する
    """
    if isinstance(data, dict):
        if "body" in data:
            results.append("> " + data["body"])
        
        # replies や children を探索
        for key in ["replies", "children", "data"]:
            if key in data:
                extract_all_bodies_recursive(data[key], results)
    
    elif isinstance(data, list):
        for item in data:
            extract_all_bodies_recursive(item, results)

def group_comments_by_parent(json_data):
    """
    第2階層（親コメント）単位でリストにまとめる
    """
    grouped_results = []

    # RedditのJSONは通常 [リスティング1, リスティング2] の形式
    # 2番目の要素にコメントが含まれる
    if isinstance(json_data, list) and len(json_data) > 1:
        comments_listing = json_data[1]
    else:
        comments_listing = json_data

    # トップレベルのコメント（children）を取得
    top_level_children = comments_listing.get("data", {}).get("children", [])

    for child in top_level_children:
        parent_branch_bodies = []
        # この親コメントとその配下の全てのbodyを回収
        extract_all_bodies_recursive(child, parent_branch_bodies)
        
        if parent_branch_bodies:
            grouped_results.append(parent_branch_bodies)
            
    return grouped_results


if __name__ == "__main__":

    url = "https://www.reddit.com/r/CreepyWikipedia/comments/1mqk72p/in_the_4th_century_there_was_supposedly_a_man/"
    text = get_text_from_included_url(url)

    print(text)