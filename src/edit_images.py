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

    pos_list = ["top", "center", "bottom"]
    load_dir = f"data/reddit/subreddit/{sys.argv[1]}/results/checked/"
    subdir_list = [subdir.replace("\\", "/") + "/" for subdir in glob(load_dir + "*")]

    for subdir in subdir_list:
        flag = False
        for pos in pos_list:
            if not os.path.exists(subdir + pos):
                flag = True
        print(f"{subdir} -> {flag}")
        if flag:
            path_list = glob(subdir + "*.png")
            for i, path in enumerate(path_list):
                print(path)
                filename = os.path.basename(path)
                image = Image.open(path)
                for pos in pos_list:
                    save_dir = path.replace(filename, "")
                    save_dir += f"{pos}/"
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    crop_image(image, position=pos).save(save_dir + filename)
