import pandas as pd
pd.options.mode.chained_assignment = None

from sqlalchemy import *
import requests
from datetime import datetime, timedelta
import gzip
import shutil
import os
import sys
import argparse

from tqdm import tqdm
tqdm.pandas()

from fuzzywuzzy import process, fuzz
import tldextract
import dask


def cwd():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def download(url: str, fname: str):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open(fname, 'wb') as file, tqdm(desc=f"\nDownloading GDELT data for {date.strftime('%Y-%m-%d %H:%M:%S')}",
                                            total=total,
                                            unit='iB',
                                            unit_scale=True,
                                            unit_divisor=1024,
                                        ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

@dask.delayed
def get_GDELT_data(date_string):

    # if not os.path.exists(f"{cwd()}/data"):
    try:
        os.mkdir(f"{cwd()}/data")
    except:
        pass

    url = f"http://data.gdeltproject.org/gdeltv3/gfg/alpha/{date_string}.LINKS.TXT.gz"

    filename = f"data/{url.split('/')[-1]}"

    download(url, filename)

    print(f"Saved {filename.split('/')[1]}...")
        
    fileout = filename.split(".")[0] + ".txt"

    with gzip.open(filename, 'rb') as f_in:
        with open(fileout, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(filename)

    print(f"Deleted {filename.split('/')[1]} and saved {fileout.split('/')[1]}...")

    return fileout

@dask.delayed
def populate_sql(file):
    print(f"\nCreating SQLite DB...")

    j = 1
    chunksize = 10000
    db_file = f"{file.split('.')[0]}.db"

    if os.path.exists(db_file):
        os.remove(db_file)

    db_path = f"sqlite:///{db_file}"
    urls_database = create_engine(db_path)

    for df in tqdm(pd.read_csv(file, chunksize=chunksize, iterator=True, 
                        sep='\t', header=None, error_bad_lines = False), total = 1000):
        df.columns = ['Date', 'FrontPageURL', 'LinkID', 'LinkPerc', 'LinkURL', 'LinkText']  
        df.index += j
        df.to_sql("urls_table", urls_database, if_exists='append')
        j = df.index[-1] + 1


    urls_database.execute("CREATE INDEX urls_index ON urls_table(FrontPageURL)")

    os.remove(file)

    print(f"DB file {db_file} saved")
    return db_path

def extract_domain(url):
    try:
        extract = tldextract.extract(url)
        return '.'.join(extract)
    except:
        return

def get_target_sources(filepath = None):
    if filepath == None:
        filepath = f'{cwd()}/sources_emm.csv'

    target_sources = pd.read_csv(filepath, delimiter='\t', keep_default_na=False)
    target_sources["top_level_domain"] = [extract_domain(url) for url in target_sources.url]
    target_sources = target_sources[pd.notna(target_sources['top_level_domain'])]

    return target_sources

def get_matches(match_row, idx_LU = get_target_sources()):
    to_match_url = match_row.gdelt_url
    to_match_tld = match_row.top_level_domain
    LU = list(idx_LU.url)

    if to_match_url in LU:
        return (LU.index(to_match_url), to_match_url, 100.0)
    else:
        filtered_LU = list(idx_LU[idx_LU.top_level_domain == to_match_tld].url)
        match = process.extractOne(to_match_url, filtered_LU, scorer = fuzz.ratio)
        return (LU.index(match[0]), match[0], match[1])

@dask.delayed
def match_urls(db_file, target_sources_path):  

    urls_database = create_engine(db_file)

    print("\nGetting target sources...")
    target_sources = get_target_sources(target_sources_path)

    print("\nMatching target and GDELT URLs...")
    query = """SELECT DISTINCT FrontPageURL FROM urls_table"""
    unique_frontPage_urls = pd.read_sql_query(query, urls_database)
    unique_frontPage_urls['top_level_domain'] = [extract_domain(url) for url in unique_frontPage_urls.FrontPageURL]

    common = sorted(set(target_sources["top_level_domain"]).intersection(set(unique_frontPage_urls["top_level_domain"])))

    common_urls = unique_frontPage_urls[unique_frontPage_urls["top_level_domain"].isin(common)].reset_index(drop=True)
    common_urls.columns = ["gdelt_url"]+list(common_urls.columns[1:])

    # tqdm.pandas()

    matched_urls = common_urls.copy()
    matched_urls["matched_idx"], matched_urls["emm_url"], matched_urls["match_score"] = zip(*common_urls.apply(get_matches, axis = 1))

    matched_urls = matched_urls[matched_urls.match_score >= 97.0] \
                    .sort_values('match_score', ascending=False) \
                    .drop_duplicates('matched_idx', keep="first") \
                    .set_index("matched_idx").sort_index()

    res = target_sources.iloc[matched_urls.index,:]
    res['gdelt_url'] = matched_urls.gdelt_url
    res.reset_index(inplace=True)

    return res
    

def get_article_links(source, urls_database):
    gdelt_url = f'"{source.gdelt_url}"'
    tld = source.top_level_domain
    query = f"""SELECT LinkURL FROM urls_table WHERE FrontPageURL = {gdelt_url}"""
    links = pd.read_sql_query(query, urls_database)
    links['top_level_domain'] = links['LinkURL'].map(extract_domain)
    return list(set(links[links.top_level_domain == tld].LinkURL))

@dask.delayed
def collect_urls(matched, db_file):
    print("\nCollecting article URLs...")
    urls_database = create_engine(db_file)
    res = matched.copy()
    res['article_links'] = res.apply(lambda x: get_article_links(x, urls_database), axis=1)
    return res

@dask.delayed
def save_urls(urls, date_string):
    urls_path = f"{cwd()}/data/{date_string}_urls.pkl"
    print(f"\nSaving URLs to {urls_path}...")
    urls.to_pickle(urls_path)
    return urls_path


def get_urls (dates, target_sources_path = None):
    res = []
    for date in dates:
        
        date_string = date.strftime("%Y%m%d%H%M%S")

        db_path = f"data/{date_string}.db"
        if os.path.exists(db_path):
            db_file = f"sqlite:///{db_path}"
            print(f"\tDB file {db_file} exists! Continuing...")
        else:
            filename = get_GDELT_data(date_string)
            db_file = populate_sql(filename)
            

        
        matched = match_urls(db_file, target_sources_path)
        # res.append(matched)
        
        urls = collect_urls(matched, db_file)
        # res.append(urls)

        urls_path = save_urls(urls, date_string)
        res.append(urls_path)

    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", required=True, type=int,
                        help="the start date of the period to collect (yyyymmdd)")
    parser.add_argument("--num_days", required=True, type=int,
                        help="num days from start date to collect")
    parser.add_argument("--time_of_day", required=False, type=int, default = 9,
                        help="time of day to collect links (only whole hours in 24h format)")
    args = parser.parse_args()

    start_date = datetime.strptime(str(args.start_date), "%Y%m%d")
    start_date = start_date.replace(hour = args.time_of_day)
    num_days = args.num_days
    dates = [start_date + timedelta(i) for i in range(num_days)]
    print(dates)

    # dask.visualize(get_urls(dates), filename='graph.svg')
    out = dask.compute(get_urls(dates))
    # print(out)
    