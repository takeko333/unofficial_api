import sys
import os
from glob import glob
from PIL import Image

def crop_image(image, position='center', target_size=(1280, 720)):
    w, h = image.size
    crop_w = w
    crop_h = w * 9 // 16
    if position == 'top':
        upper = 0
    elif position == 'bottom':
        upper = h - crop_h
    else:
        upper = (h - crop_h) // 2
    lower = upper + crop_h
    image = image.crop((0, upper, w, lower))
    image = image.resize(target_size, Image.LANCZOS)
    return image

if __name__ == "__main__":

    load_dir = f"data/reddit/subreddit/{sys.argv[1]}/results/checked/{sys.argv[2]}/"
    path_list = glob(load_dir + "*.png")

    for i, path in enumerate(path_list):
        print(path)
        filename = os.path.basename(path)
        image = Image.open(path)
        for pos in ["top", "center", "bottom"]:
            save_dir = path.replace(filename, "")
            save_dir += f"{pos}/"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            crop_image(image, position=pos).save(save_dir + filename)
