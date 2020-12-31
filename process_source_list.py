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

def get_source_locations(source_file):
  source_df = pd.read_csv(source_file, delimiter='\t', keep_default_na=False)

  tqdm.pandas(desc = "Getting source locations")
  latlon = source_df.progress_apply(call_geocoding, axis = 1)

  source_df["lat"], source_df["lon"] = list(zip(*latlon))
  source_df.to_csv("processed_sources.csv", sep='\t', encoding='utf-8', index = False)

  null_locs = source_df[source_df['lat'].isnull()]
  print(f"{(len(source_df)-len(null_locs))*100/len(source_df)}% of source locations found")
  print(f"Distribution of missing loactions by country:\n{null_locs['country'].value_counts()}")


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

    # np.random.seed()
    # sleeptime = np.random.uniform(1, 2)
    # time.sleep(sleeptime)
    # print(f"Sleeping {sleeptime}s")

    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    try:
      s = requests.Session()
      retries = Retry(total=5,
                      backoff_factor=4,
                      status_forcelist=[500, 502, 503, 504])
      s.mount('http://', HTTPAdapter(max_retries=retries))

      resp = s.get(url=url, headers = headers)
      text = resp.json()
    except Exception as e:
      print(f"ERROR! Unable to get location: {e}")
      return (None, None)

    try:
      lat = text[0]['lat']
      lon = text[0]['lon']
    except:
      return (None, None)

    # print(f"Success! {lat}, {lon}")
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
