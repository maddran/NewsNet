from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import json

def get_source_locations(source_df):
    api_key = input("Enter API key for Google GeoCoding API (Hit Enter to skip):")
    if api_key:
        tmp = source_df.apply(lambda x: call_geocoding(x, api_key), axis=1)
        source_df["lat"], source_df['lon'] = list(zip(*tmp))
            
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

if __name__ == "__main__":
    
    source_df = pd.read_csv(args.source_file, delimiter='\t', keep_default_na=False)

    if 'lat_lon' not in source_df.columns:
        get_source_locations(source_df)