import pandas as pd
import numpy as np
import argparse
import os, sys
import tldextract
from datetime import datetime, timedelta

def get_links(i, file, source_tlds):
    try:
        df = pd.read_pickle(file)
    except:
        print(f"Count not load file {file}. Continuing...")
        return
    df = df[df['parsed_article'].notna()]
    df_articles = pd.DataFrame(df['parsed_article'].values.tolist(), index = df.index)
    df_res = pd.concat([df.loc[:,['index', 'top_level_domain','topic1', 'topic2']],
                        df_articles.loc[:,['external_links', 'parsed_date']]], axis = 1)
    df_res = df_res[df_res['external_links'].notna()]
    df_res = df_res.explode('external_links').reset_index(drop=True)
    df_res = df_res[df_res['external_links'].isin(source_tlds.keys())]
    df_res.columns = ['from_index', 'from_tld', 'topic1', 'topic2', 'to_tld', 'parsed_date']
    df_res['to_index'] = [source_tlds[tld] for tld in df_res['to_tld']]

    print(f"\nDone {i+1} files. {len(df_res)} total links found in {file}")

    return df_res.loc[:, ['from_index', 'to_index', 'parsed_date', 'topic1', 'topic2']]

def get_source_tlds(df):
    tlds = list(df['url'].apply(extract_domain))
    return dict(zip(tlds, df.index))

def extract_domain(url):
    try:
        extract = tldextract.extract(url)
        return '.'.join(extract)
    except:
        return


def truncate_date(dt):
    try:
        res = np.datetime64(dt, 'D')
        # res = dt.value.astype('<M8[D]')
    except Exception as e:
        # print(dt, e)
        res = np.nan

    return res

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parsed_files", required=True, type=lambda x: is_valid_file(parser, x),
                        nargs='+', help="full path of the parsed files to generate a network from")
    parser.add_argument("--source_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the csv file containing the source list")
    parser.add_argument("--start_date", required=False, type=int,
                        help="start date of period being analysed as integer in YYYYmmdd format - used to sense check parsed dates")
    parser.add_argument("--num_days", required=False, type=int,
                        help="number of days in period being analysed")

    args = parser.parse_args()

    if args.start_date and (args.num_days is None):
        parser.error("--start_date argument also requires --num_days!")

    if not os.path.exists("edgelist/"):
        os.makedirs("edgelist")

    source_df = pd.read_csv(args.source_file, delimiter='\t', keep_default_na=False)

    source_tlds = get_source_tlds(source_df)

    print(f"\nProcessing {len(args.parsed_files)} total files:")
    link_dfs = [get_links(i, file, source_tlds) for i, file in enumerate(args.parsed_files)] 
    links_df = pd.concat(link_dfs, axis=0)
    
    links_df["parsed_date"] = pd.to_datetime(links_df["parsed_date"], errors='coerce', utc=True).dt.tz_localize(None)

    if args.start_date:
        print(
                f'\nPre-trim: min = {min(links_df.parsed_date.dropna())} '
                f'max = {max(links_df.parsed_date.dropna())} ',
                f'nans = {links_df.parsed_date.isna().sum()} '
        )
        start_date = datetime.strptime(str(args.start_date), '%Y%m%d')
        end_date = start_date + timedelta(days=args.num_days)
        
        start_date = start_date - timedelta(366)
        end_date = end_date + timedelta(90)

        mask = (links_df['parsed_date'] < start_date) | (links_df['parsed_date'] > end_date)
        links_df.loc[mask, 'parsed_date'] = np.nan    

        print(
                f'\nPost-trim: min = {min(links_df.parsed_date.dropna())} '
                f'max = {max(links_df.parsed_date.dropna())} ',
                f'nans = {links_df.parsed_date.isna().sum()} '
        )

    links_df["parsed_date"] = links_df["parsed_date"].apply(truncate_date)

    parsed_date_prop = 100*(1-(links_df.parsed_date.isna().sum()/len(links_df)))
    print(f"\n{len(links_df)} total links found. {round(parsed_date_prop,2)}% of publish dates found.")

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    links_df.to_csv(f"edgelist/edgelist_{now}.csv", index=False)
    print(links_df.sample(10))
