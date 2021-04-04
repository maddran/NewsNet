import argparse
import os
import sys
from glob import glob

import pandas as pd
import pickle
from tqdm import tqdm 
from multiprocessing import Pool, cpu_count

from text_helpers import predict_pipeline

def get_topics(fp):
    with open(fp, "rb") as pfile:
        df = pickle.load(pfile)

    text = [' '.join([sub['title'], sub['text']]) 
            for sub in df.parsed_article if sub]

    pred1, pred2 = predict_pipeline(text[:1000])
    print(pred1, pred2)


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", required=True, type=lambda x: is_valid_file(parser, x),
                        nargs='+', help="full path of the parsed files to generate a network from")

    args = parser.parse_args()
    fps = args.files

    with Pool(cpu_count()) as pool:
        _ = pool.map(get_topics, args.files)
    
    # [get_topics(fp) for fp in fps]
