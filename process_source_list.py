import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import argparse
import os

def get_source_locations(source_df):
    tmp = source_df.apply(lambda x: call_geocoding(x), axis=1)
    source_df["lat_lon"] = list(tmp)

    source_df.to_csv("processed_sources.csv", sep='\t', encoding='utf-8')
            

def call_geocoding(row):
    name = row["text"]  # + " news"
    country = row["country"]

    query = '+'.join(name.split() + country.split())
    latlon = get_latlon(row, query)

    if not all(latlon):
      query = '+'.join(country.split())
      latlon = get_latlon(row, query)

    return latlon


def get_latlon(row, query):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&country={row['country']}&countrycodes={row['country_short']}"
    resp = requests.get(url=url)
    text = resp.json()

    try:
      lat = text[0]['lat']
      lon = text[0]['lon']
    except:
      return (None, None)

    return (lat, lon)


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
    source_df = pd.read_csv(args.source_file, delimiter='\t', keep_default_na=False)

    if 'lat_lon' not in source_df.columns:
        get_source_locations(source_df)
