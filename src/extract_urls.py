import sys
import json
from tqdm import tqdm

def get_urls_and_tags(data, word):
    urls = []
    tags = []
    for item in tqdm(data):
        url = item["data"]["url"]
        tag_info = item["data"]["link_flair_richtext"]
        if len(tag_info) != 0:
            tag = item["data"]["link_flair_richtext"][0]["t"]
        else:
            tag = "None"
        if word in url:
            urls.append(url)
            tags.append(tag)
    return urls, tags

if __name__ == "__main__":

    base_dir = f"data/reddit/subreddit/{sys.argv[1]}/"

    words = {
        "CreepyWikipedia": "wikipedia.org", 
        "Paranormal": "www.reddit.com/r/Paranormal/", 
    }

    with open(base_dir + "posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = []
    urls, tags = get_urls_and_tags(data, words[sys.argv[1]])
    with open(base_dir + "used_urls.txt", "r", encoding="utf-8") as f:
        used_urls = [line.replace("\n", "") for line in f.readlines()]
    for url, tag in zip(urls, tags):
        if url not in used_urls:
            lines.append(f"{url}, {tag}\n")

    with open(base_dir + "urls.txt", "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line)