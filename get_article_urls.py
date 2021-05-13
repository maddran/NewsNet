import pandas as pd
pd.options.mode.chained_assignment = None

from sqlalchemy import *
import requests
from datetime import datetime, timedelta
import gzip
import shutil
import os, sys, glob
import argparse
from tqdm import tqdm
from fuzzywuzzy import process, fuzz
import tldextract
import dask
from dask.distributed import Client
from collections import Counter

def sprint(string):
    sys.stdout.write(string)

def cwd():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def tmp():
    return os.environ.get('LOCAL_SCRATCH')

def download(url: str, fname: str):
    resp = requests.get(url, stream=True)
    # with open(fname, 'wb') as file:
    #     for data in resp.iter_content(chunk_size=1024):
    #         file.write(data)


    total = int(resp.headers.get('content-length', 0))
    with open(fname, 'wb') as file, tqdm(desc=f"Downloading {fname.split('/')[-1]}",
                                            position=0,
                                            total=total,
                                            unit='iB',
                                            unit_scale=True,
                                            unit_divisor=1024,
                                        ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def populate_sql(file, wrkdir, date_string):
    
    j = 1
    chunksize = int(1e6)
    db_file = f"{tmp()}/{date_string}.db"

    tmp_db_path = f"sqlite:///{db_file}"
    urls_database = create_engine(tmp_db_path)

    sprint(f"\n\nCreating SQLite DB from {file} at {tmp_db_path}...")

    chunks = pd.read_csv(file, chunksize=chunksize, iterator=True, quoting=3, engine='python',
                         sep='\t', header=None, error_bad_lines=False, warn_bad_lines=False)

    try:
        for df in tqdm(chunks, desc=f"Populating {tmp_db_path.split('/')[-1]}", total = 10):
            df.columns = ['Date', 'FrontPageURL', 'LinkID', 'LinkPerc', 'LinkURL', 'LinkText']  
            df.index += j
            df.to_sql(f"urls_table", urls_database, if_exists='append')
            j = df.index[-1] + 1
    except Exception as e:
        print(f"{e}\n\nUnable to parse {file}. Continuing...")
        return

    try:
        urls_database.execute(f"CREATE INDEX urls_index ON urls_table(FrontPageURL)")
    except Exception as e:
        print(f"{e}\n\nContinuing...")

    os.remove(file)
    final_db_path = f"{wrkdir}/tmp/{date_string}.db"
    shutil.move(tmp_db_path.split('sqlite:///')[-1], 
                final_db_path)

    sprint(f"\n\nDB file {final_db_path.split('/')[-1]} saved")
    return final_db_path

def extract_domain(url):
    try:
        extract = tldextract.extract(url)
        return '.'.join(extract)
    except:
        return

def get_target_sources(filepath = None):
    if filepath == None:
        filepath = f'{cwd()}/sources_emm.csv'

    sprint(f"\n\nGetting target sources from {filepath}...\n")

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

def get_article_links(source, urls_database, date_string):
    gdelt_url = f'"{source.gdelt_url}"'
    tld = source.top_level_domain
    query = f"""SELECT LinkURL FROM urls_table WHERE FrontPageURL = {gdelt_url}"""
    links = pd.read_sql_query(query, urls_database)
    links['top_level_domain'] = links['LinkURL'].map(extract_domain)
    return list(set(links[links.top_level_domain == tld].LinkURL))


@dask.delayed
def get_GDELT_data(tmpdir, wrkdir, date_string):

    url = f"http://data.gdeltproject.org/gdeltv3/gfg/alpha/{date_string}.LINKS.TXT.gz"

    filename = f"{tmpdir}/{url.split('/')[-1]}"

    download(url, filename)

    sprint(f"\n\nSaved {filename}...")

    fileout = filename.split(".")[0] + ".txt"

    with gzip.open(filename, 'rb') as f_in:
        with open(fileout, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(filename)

    sprint(
        f"\n\nDeleted {filename.split('/')[-1]} and saved {fileout.split('/')[-1]}...")

    db_path = populate_sql(fileout, wrkdir, date_string)
    db_url = f"sqlite:///{db_path}"

    return db_url

@dask.delayed
def match_urls(db_file, target_sources_path, date_string):  

    urls_database = create_engine(db_file)

    target_sources = get_target_sources(target_sources_path)

    sprint("\n\nMatching target and GDELT URLs...\n")
    query = f"""SELECT DISTINCT FrontPageURL FROM urls_table"""
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

@dask.delayed
def collect_urls(matched, db_file, date_string):
    print("\n\nCollecting article URLs...")
    urls_database = create_engine(db_file)
    res = matched.copy()
    res['article_links'] = res.apply(lambda x: get_article_links(x, urls_database, date_string), axis=1)
    return res

@dask.delayed
def save_urls(urls, urls_path):
    print(f"\n\nSaving URLs to {urls_path}...")
    urls.to_pickle(urls_path)
    return urls_path

def dropDups(row, threshold = 2):

    combined_links = row['combined_links']
    to_prune = row['article_links']

    counts = Counter(combined_links)
    # print(counts.most_common(10))
    row['article_links'] = [k for k,v in counts.items() if (k in to_prune and v < threshold)]

    return row

def pruneLinks(urlfiles):
    to_prune = pd.read_pickle(urlfiles[-1]).set_index("index")
    num_links = sum(to_prune["article_links"].apply(len))

    for urlfile in urlfiles[:-1]:
        df = pd.read_pickle(urlfile)
        df.set_index("index", inplace = True)

        temp = to_prune.join(df['article_links'], lsuffix='', rsuffix='_new')
        temp = temp.applymap(lambda d: d if isinstance(d, list) else [])

        to_prune['combined_links'] = temp['article_links']+temp['article_links_new']
    
    pruned = to_prune.apply(dropDups, axis = 1)
    pruned.drop('combined_links', axis=1, inplace = True)

    pruned["num_links"] = pruned["article_links"].apply(len)
    pruned = pruned[pruned.num_links > 0]

    pruned_path = f"{urlfiles[-1].split('.')[0]}_pruned.pkl"
    pruned_path = pruned_path.replace('raw_urls', 'pruned_urls')
    pruned.to_pickle(pruned_path)

    num_links_pruned = sum(pruned["num_links"])
    sprint(f"\n\nPruned {round((num_links - num_links_pruned)/num_links, 2)*100} % of URLs ({num_links_pruned} total URLs left).")
    sprint(f"Saving pruned URLs to {pruned_path}...")

    return pruned


def get_urls(dates, target_sources_path=None):
    res = []
    wrkdir = os.path.dirname(cwd())
    os.makedirs(f"{wrkdir}/tmp", exist_ok=True)
    os.makedirs(f"{wrkdir}/data", exist_ok=True)

    if tmp():
        tmpdir = tmp()
    else:
        tmpdir = f"{wrkdir}/tmp"

    for date in dates:
        date_string = date.strftime("%Y%m%d%H%M%S")

        db_path = f"{wrkdir}/tmp/{date_string}.db"
        urls_path = f"{wrkdir}/data/raw_urls/{date_string}_urls.pkl"
        if os.path.exists(urls_path):
            print(f"\n\tURL file {date_string}_urls.pkl exists! Continuing...")
        else:
            if os.path.exists(db_path):
                db_url = f"sqlite:///{db_path}"
                print(f"\n\tDB file {db_path} exists! Continuing...")
            else:
                db_url = get_GDELT_data(tmpdir, wrkdir, date_string)

            matched = match_urls(db_url, target_sources_path, date_string)
            urls = collect_urls(matched, db_url, date_string)
            urls_path = save_urls(urls, urls_path)

        res.append(urls_path)

    return res


def main(args):

    start_date = datetime.strptime(str(args.start_date), "%Y%m%d")
    start_date = start_date.replace(hour=args.time_of_day)
    num_days = args.num_days
    dates = [start_date + timedelta(i) for i in range(-2, num_days)]
    source_path = args.source_file

    res = get_urls(dates, source_path)
    if args.visualize:
        dask.visualize(*res, filename='get_article_graph.svg')
    else:
        urlfiles = dask.compute(*res)
        urlfiles = sorted(urlfiles)

        rng = list(range(len(urlfiles)))[2:]
        _ = [pruneLinks(urlfiles[i-2:i+1]) for i in rng]

    print("\n\nDone!\n\n")

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the csv file containing the source list")
    parser.add_argument("--start_date", required=True, type=int,
                        help="the start date of the period to collect (yyyymmdd)")
    parser.add_argument("--num_days", required=True, type=int,
                        help="num days from start date to collect")
    parser.add_argument("--time_of_day", required=False, type=int, default = 9,
                        help="time of day to collect links (only whole hours in 24h format)")
    parser.add_argument("--distribute", action = 'store_true',
                        help="starts local cluster")
    parser.add_argument("--visualize", action='store_true',
                        help="skips computation and outputs graph (requires graphviz installed)")
    
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    main(args)

   
    
