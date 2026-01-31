import sys
import json
from tqdm import tqdm

def get_urls(data, word):
    urls = []
    for item in tqdm(data):
        url = item["data"]["url"]
        if word in url:
            urls.append(url)
    return urls

if __name__ == "__main__":

    base_dir = f"data/reddit/subreddit/{sys.argv[1]}/"

    words = {
        "CreepyWikipedia": "wikipedia.org", 
    }

    with open(base_dir + "posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = get_urls(data, words[sys.argv[1]])

    with open(base_dir + "urls.txt", "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")