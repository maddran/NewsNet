import pandas as pd
import numpy as np
import argparse
import os

def split_file(url_file, n):
    df = pd.read_pickle(url_file)
    df = df.explode('article_links').reset_index(drop=False)
    splits = np.array_split(df, n)
    url_files =[]
    for i, s in enumerate(splits):
        filepath = f"{url_file.split('.')[0]}_{i}.pkl"
        s.to_pickle(filepath)
        url_files.append(filepath)

    nl = '\n'
    file_string = nl.join([f"{i} -> {uf}" for i, uf in enumerate(url_files)])
    print(f"{url_file} was split into {n} files:{nl}{nl}{file_string}{nl}")


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

    args = parser.parse_args()

    split_file(args.url_file, args.num_splits)
