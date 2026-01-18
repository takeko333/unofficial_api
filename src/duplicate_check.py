from glob import glob
from collections import Counter

if __name__ == "__main__":

    load_dir = "results"

    path_list = glob(f"{load_dir}/*.txt")
    filenames = [path.split("_")[-1] for path in path_list]
    for filename in filenames:
        print(filename)

    print(Counter(filenames))