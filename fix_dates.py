from parse_articles import parse_date
import argparse
import os
import sys
import pandas as pd

def fix_dates(i, file):
    df = pd.read_pickle(file)
    df = df.apply(apply_fix)

    new_file = f"{file.split('.pkl')[0]}_fixed_date.pkl"
    df = pd.to_pickle(new_file)

def apply_fix(row):
    if row['parsed_articles']['parsed_date']:
        return row
    else:
        row['parsed_articles']['parsed_date'] = parse_date(row['parsed_articles']['url'])
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

    _ = [fix_dates(i, file) for i, file in enumerate(args.parsed_files)]
