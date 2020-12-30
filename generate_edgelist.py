import pandas as pd
import argparse
import os, sys
import tldextract
from datetime import datetime

def get_links(i, file, source_tlds):
    df = pd.read_pickle(file)
    df = df[df['parsed_article'].notna()]
    df_articles = pd.DataFrame(df['parsed_article'].values.tolist(), index = df.index)
    df_res = pd.concat([df.loc[:,['index', 'top_level_domain']],
                        df_articles.loc[:,['external_links', 'parsed_date']]], axis = 1)
    df_res = df_res[df_res['external_links'].notna()]
    df_res = df_res.explode('external_links').reset_index(drop=True)
    df_res = df_res[df_res['external_links'].isin(source_tlds.keys())]
    df_res.columns = ['from_index', 'from_tld', 'to_tld', 'parsed_date']
    df_res['to_index'] = [source_tlds[tld] for tld in df_res['to_tld']]

    print(f"\nDone {i+1} files. {len(df_res)} total links found in {file}")

    return df_res.loc[:,['from_index', 'to_index', 'parsed_date']]

def get_source_tlds(df):
    tlds = list(df['url'].apply(extract_domain))
    return dict(zip(tlds, df.index))

def extract_domain(url):
    try:
        extract = tldextract.extract(url)
        return '.'.join(extract)
    except:
        return

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

    args = parser.parse_args()

    source_df = pd.read_csv(args.source_file, delimiter='\t', keep_default_na=False)

    source_tlds = get_source_tlds(source_df)

    print(f"\nProcessing {len(args.url_files)} total files:")
    link_dfs = [get_links(i, file, source_tlds) for i, file in enumerate(args.url_files)] 

    links_df = pd.concat(link_dfs, axis=0)
    # print(links_df.shape, "\n", links_df.head(10))

    if not os.path.exists("/edgelist"):
        os.makedirs("/edgelist")

    now = datetime.now().strftime("%d%m%Y_%H%M%S")
    links_df.to_csv(f"/edgelist/edgelist_{now}.csv")
