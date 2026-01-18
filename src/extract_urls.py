import json
from tqdm import tqdm

if __name__ == "__main__":

    with open("data/json/nosleep.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("urls.txt", "w", encoding="utf-8") as f:
        for item in tqdm(data):
            url = item["data"]["url"]
            if "https://" in url:
                f.write(url + "\n")