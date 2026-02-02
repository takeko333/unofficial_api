import sys
import os
import glob
from glob import glob
from PIL import Image

def crop_image(image, target_size=(1280,  720)):
    w, h = image.size
    crop_w = w
    crop_h = w * 9 // 16
    image = image.crop(((w - crop_w) // 2, (h - crop_h) // 2, (w + crop_w) // 2, (h + crop_h) // 2))
    image = image.resize(target_size)
    return image

if __name__ == "__main__":

    base_dir = sys.argv[1]
    path_list = glob(base_dir + "/*/*.png")

    for i, path in enumerate(path_list):
        print(path)
        #image = Image.open(path)
        #image.save(path)