import pandas as pd
import pickle
from glob import glob
from parse_articles import cwd

parsed_files = sorted(glob(f"{cwd()}/parsed/*parsed.pkl"))
if not parsed_files:
    parsed_files = sorted(glob(f"parsed/*parsed.pkl"))

for pf in parsed_files:
    
    df = pd.read_pickle(pf)
    parsed = df['parsed_article']
    total_articles = len(parsed)

    parsed = pd.DataFrame([p for p in list(parsed) if p])
    parsed['lang'] = df['lang_short']
    num_articles = len(parsed)
    success_rate = num_articles*100/total_articles
    date_parse_rate = sum(pd.notna(parsed['parsed_date']))*100/total_articles
    text_parse_rate = sum(pd.notna(parsed['text']))*100/total_articles

    print("\n\n", parsed.columns)

    to_translate = sum(parsed.lang != 'en')
    translated = parsed[parsed.title != parsed.translated_title]
    translation_rate = sum([p != 'ERROR' for p in translated])*100/to_translate

    sep = "-"*20
    print(f"\n{sep}{pf.split('/')[-1][:8]}{sep}")
    print(f"# of articles parsed = {num_articles}")
    print(f"parse success rate = {round(success_rate,2)}%")
    print(f"date parse success rate = {round(date_parse_rate,2)}%")
    print(f"text parse success rate = {round(text_parse_rate,2)}%")
    print(f"translation success rate = {round(translation_rate,2)}%")

    
