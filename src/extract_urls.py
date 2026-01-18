import sys
import json
from tqdm import tqdm

if __name__ == "__main__":

    base_dir = f"data/reddit/subreddit/{sys.argv[1]}/"

    with open(base_dir + "posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(base_dir + "urls.txt", "w", encoding="utf-8") as f:
        for item in tqdm(data):
            url = item["data"]["url"]
            if sys.argv[1] in url:
                f.write(url + "\n")