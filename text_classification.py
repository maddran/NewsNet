import argparse
import os
import sys
from glob import glob

import pandas as pd
import pickle
from tqdm import tqdm 
from text_helpers import predict_pipeline

def get_topics(fp):
    with open(fp, "rb") as pfile:
        df = pickle.load(pfile)

    print(df.head())
    text = [' '.join([sub['title'], sub['text']]) 
            if sub else None for sub in df.parsed_article]

    print('\n'.join(text[0:10]))
    print('DONE!')


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parsed_files", required=True, type=lambda x: is_valid_file(parser, x),
                        nargs='+', help="full path of the parsed files to generate a network from")

    args = parser.parse_args()
    print(args.parsed_files)

    get_topics(args.parsed_files[0])
