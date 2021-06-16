import pandas as pd
import pickle
from glob import glob
from itertools import groupby
from parse_articles import cwd
import numpy as np
 
parsed_files = sorted(glob(f"{cwd()}/parsed/*parsed.pkl"))
if not parsed_files:
    parsed_files = sorted(glob(f"parsed/*parsed.pkl"))

grouped_files = [list(g) for k, g in groupby(parsed_files, key=lambda x: x.split('/')[-1][:8])]

for group in grouped_files:
    num_articles = []
    success_rate = []
    date_parse_rate = []
    text_parse_rate = []

    for pf in group:    
        try:
            df = pd.read_pickle(pf)
            parsed = df['parsed_article']
            total_articles = len(parsed)

            parsed = pd.DataFrame([p for p in list(parsed) if p])
            num_articles = num_articles+[len(parsed)]
            success_rate = success_rate + [num_articles*100/total_articles]
            date_parse_rate = date_parse_rate + [sum(pd.notna(parsed['parsed_date']))*100/total_articles]
            text_parse_rate = text_parse_rate + [(pd.notna(parsed['text']))*100/total_articles]
        except:
            print(f"Unable to read {pf}. Continuing...")

            

    # print("\n\n", parsed.columns)

    sep = "-"*20
    print(f"\n{sep}{pf.split('/')[-1][:8]}{sep}")
    print(f"# of articles parsed = {np.mean(num_articles)}")
    print(f"parse success rate = {round(np.mean(success_rate),2)}%")
    print(f"date parse success rate = {round(np.mean(date_parse_rate),2)}%")
    print(f"text parse success rate = {round(np.mean(text_parse_rate),2)}%")


    
