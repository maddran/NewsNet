import pandas as pd
import pickle
from glob import glob
from parse_articles import cwd

parsed_files = sorted(glob(f"{cwd()}/parsed/*parsed.pkl"))

for pf in parsed_files:
    parsed = pd.read_pickle(pf)
    num_articles = len(parsed)

    sep = "-"*20
    print(f"\n{sep}{pf.split('/')[-1][:8]}{sep}")
    print(f"# of articles parsed = {num_articles}")
    print(parsed.columns)#['parsed_dates'].value_counts())
