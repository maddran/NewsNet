import pandas as pd
import pickle
from glob import glob
from parse_articles import cwd

parsed_files = sorted(glob(f"{cwd()}/parsed/*parsed.pkl"))
if not parsed_files:
    parsed_files = sorted(glob(f"parsed/*parsed.pkl"))

for pf in parsed_files:
    
    parsed = pd.read_pickle(pf)['parsed_article']
    total_articles = len(parsed)

    parsed = pd.DataFrame([p for p in list(parsed) if p])
    num_articles = len(parsed)
    success_rate = num_articles*100/total_articles
    date_parse_rate = sum(pd.notna(parsed['parsed_date']))*100/total_articles
    text_parse_rate = sum(pd.notna(parsed['text']))*100/total_articles
    translation_rate = sum([p != 'ERROR' for p in parsed['parsed_date']])*100/total_articles

    sep = "-"*20
    print(f"\n{sep}{pf.split('/')[-1][:8]}{sep}")
    print(f"# of articles parsed = {num_articles}")
    print(f"parse success rate = {round(success_rate,2)}%")
    print(f"date parse success rate = {round(date_parse_rate,2)}%")
    print(f"text parse success rate = {round(text_parse_rate,2)}%")
    print(f"translation success rate = {round(translation_rate,2)}%")

    print("\n\n",parsed.head())
