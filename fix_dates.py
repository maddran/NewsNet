from htmldate import find_date
import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm 
from multiprocessing import Pool, cpu_count

def fix_dates(file):
    new_file = f"{file.split('.pkl')[0]}_fixed_date.pkl"
    if os.path.exists(new_file):
        return

    df = pd.read_pickle(file)

    tqdm.pandas(desc=file)
    df = df.progress_apply(apply_fix, axis = 1)
    
    df.to_pickle(new_file)

def apply_fix(row):
    if row['parsed_article']:
        if row['parsed_article']['parsed_date']:
            pass
        else:
            row['parsed_article']['parsed_date'] = find_date(row['parsed_article']['url'])
    else:
        pass
    return row

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

    with Pool(min(5, cpu_count()) as pool:
        _ = pool.map(fix_dates, args.parsed_files)
