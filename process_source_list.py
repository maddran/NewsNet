import requests
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import json
import pandas as pd
import argparse
import os
from tqdm.auto import tqdm
import numpy as np
import time

# from multiprocessing import Pool, cpu_count
# def get_source_locations_mp(source_file):
#   source_df = pd.read_csv(source_file, delimiter='\t', keep_default_na=False).head(200)
#   num_processes = cpu_count()
#   chunks = chunk_df(source_df, num_processes)

#   res = []
#   with Pool(processes=num_processes) as p:
#     for r in tqdm(p.imap(call_geocoding, chunks), total=len(chunks), desc="Getting source locations: "):
#       res.append(r)
  
#   source_df["lat_lon"] = [val for sublist in res for val in sublist]
#   source_df.to_csv("processed_sources.csv", sep='\t', encoding='utf-8')


# def chunk_df(df, num_processes):
#   chunks = np.array_split(df, max(10, num_processes))
#   return chunks

def get_source_locations(source_file):
  source_df = pd.read_csv(source_file, delimiter='\t',
                          keep_default_na=False).head(200)

  tqdm.pandas()
  source_df["lat_lon"] = source_df.progress_apply(call_geocoding, axis = 1)
  source_df.to_csv("processed_sources.csv", sep='\t', encoding='utf-8')


def call_geocoding(row):
  name = row["text"]
  country = row["country"]

  query = '+'.join(name.split() + country.split())
  latlon = get_latlon(row, query)

  if not all(latlon):
    query = '+'.join(country.split())
    latlon = get_latlon(row, query)

  return latlon


def get_latlon(row, query):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&country= \
            {row['country']}&countrycodes={row['country_short']}"

    np.random.seed()
    sleeptime = np.random.uniform(1, 2)
    time.sleep(sleeptime)
    # print(f"Sleeping {sleeptime}s")

    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    try:
      s = requests.Session()
      retries = Retry(total=5,
                      backoff_factor=4,
                      status_forcelist=[500, 502, 503, 504, 111])
      s.mount('http://', HTTPAdapter(max_retries=retries))

      resp = s.get(url=url, headers = headers)
      text = resp.json()
    except Exception as e:
      print(e, "\n", resp)
      return (None, None)

    try:
      lat = text[0]['lat']
      lon = text[0]['lon']
    except:
      return (None, None)

    print(f"Success! {lat}, {lon}")
    return (float(lat), float(lon))


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the csv file containing the source list")

    args = parser.parse_args()
    get_source_locations(args.source_file)
