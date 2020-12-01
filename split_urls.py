import pandas as pd
import numpy as np
import argparse

def split_file(url_file, n):
    df = pd.read_pickle(url_file)
    df = df.explode('article_links').reset_index(drop=False)
    splits = np.array_split(df, n)
    url_files =[]
    for i, s in enumerate(splits):
        filepath = f"{url_file.split('.')[0]}_{i}.pkl"
        s.to_pickle(filepath)
        url_files.append(filepath)

    print(f"{url_file} was split into {n} files {url_files}")


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_splits", required=True, type=int,
                        help="number of files to split into")
    parser.add_argument("--url_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the url file to be parsed")