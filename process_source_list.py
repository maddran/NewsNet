import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import argparse
import os
from tqdm.auto import tqdm
from multiprocessing import Pool, cpu_count
import numpy as np

def get_source_locations(source_file):
  source_df = pd.read_csv(source_file, delimiter='\t', keep_default_na=False)
  num_processes = cpu_count()
  chunks = chunk_df(source_df, num_processes)

  res = []
  with Pool(processes=num_processes) as p:
    for r in tqdm(p.imap(call_geocoding, chunks), total=len(chunks), desc="Getting source locations: "):
      res.append(r)
  
  source_df["lat_lon"] = [val for sublist in res for val in sublist]
  source_df.to_csv("processed_sources.csv", sep='\t', encoding='utf-8')

  # print(res) 
    
def chunk_df(df, num_processes):
  chunks = np.array_split(df, max(10,num_processes))
  return chunks

def call_geocoding(df):
  res = []
  for row in df.iterrows():
    row = row[1]
    name = row["text"]  # + " news"
    country = row["country"]

    query = '+'.join(name.split() + country.split())
    latlon = get_latlon(row, query)

    if not all(latlon):
      query = '+'.join(country.split())
      latlon = get_latlon(row, query)

    res.append(latlon)
  return res


def get_latlon(row, query):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&country={row['country']}&countrycodes={row['country_short']}"
    resp = requests.get(url=url)
    text = resp.json()

    try:
      lat = text[0]['lat']
      lon = text[0]['lon']
    except:
      return (None, None)

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
