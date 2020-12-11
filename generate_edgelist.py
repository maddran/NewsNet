import pandas as pd
import argparse
import os, sys
import tldextract
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import json

def get_links(file, source_tlds):
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

def get_source_locations(source_df):
    api_key = input("Enter API key for Google GeoCoding API (Hit Enter to skip):")
    if api_key:
            
def call_geocoding(row, api_key):
    name = row["text"] + " news"
    country = row["country"]
    query = '+'.join(name.split() + country.split())

    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={api_key}'

    jsonurl = urlopen(url)

    text = json.loads(jsonurl.read())
    lat = text['results'][0]["geometry"]['location']["lat"]
    lon = text['results'][0]["geometry"]['location']["lon"]

    return (lat, lon)


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_files", required=True, type=lambda x: is_valid_file(parser, x),
                        nargs='+', help="full path of the parsed files to generate a network from")
    parser.add_argument("--source_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the csv file containing the source list")

    args = parser.parse_args()

    source_df = pd.read_csv(args.source_file, delimiter='\t', keep_default_na=False)

    if 'lat_lon' not in source_df.columns:
        get_source_locations(source_df)

    source_tlds = get_source_tlds(source_df)

    link_dfs = [get_links(file, source_tlds) for file in args.url_files] 

    links_df = pd.concat(link_dfs, axis=0)
    print(links_df.shape, "\n", links_df.head(10))