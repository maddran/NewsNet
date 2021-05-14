import os, sys
import argparse
from newspaper import Article
from urllib.parse import urljoin
import tldextract
from dateparser import parse as dateparse
from googletrans import Translator
from bs4 import BeautifulSoup
from tqdm import tqdm
import dask
import dask.dataframe as dd
from collections import Counter
import glob
import pandas as pd
from datetime import datetime
import pickle
from htmldate import find_date

def sprint(string):
    sys.stdout.write(string)

def cwd():
    return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))

# @dask.delayed
def parse_html(article):
    soup = BeautifulSoup(article['html'], features="lxml")

    if article["date"] == None:
        # parsed_date = parse_date(soup)
        # if parsed_date:
        #     try:
        #         parsed_date = dateparse(parsed_date)
        #     except:
        #         parsed_date = None

        article["parsed_date"] = parse_date(article)
    else:
        article["parsed_date"] = article['date']

    article['raw_links'] = get_links(soup)
    article = process_links(article)

    return article


def parse_date(article):
    try:
        date = find_date(article['url'])
    except Exception as e:
        print(e)
        date = None

    return date
    



def parse_date_tag(tag):
    try:
      date = tag['datetime']
      if (not date or date.isspace()):
        raise
    except:
      try:
        date = tag['content']
        if (not date or date.isspace()):
          raise
      except:
        date = tag.get_text()

    if (not date or date.isspace()):
      return None
    else:
      # print(f"\n\nFOUND TIME TAG: {date}")
      return date


def get_links(soup):
    links = soup.find_all('a', href=True)
    links = [l['href'] for l in links]
    return links


def extract_domain(url):
    try:
        extract = tldextract.extract(url)
        return '.'.join(extract)
    except:
        return

def try_urljoin(url, rl):
    try:
        return urljoin(url, rl)
    except:
        return

# @dask.delayed
def process_links(article):
    raw_links = article["raw_links"]
    url = article["url"]
    tld = extract_domain(url)

    links = [try_urljoin(url, rl) for rl in raw_links]
    links = list(set([extract_domain(l) for l in links]))
    internal = [l for l in links if l == tld]
    external = [l for l in links if l != tld]

    article['links'] = links
    article['internal_links'] = internal
    article['external_links'] = external

    return article

# @dask.delayed
def get_article(url):
    
    article = Article(url, keep_article_html=True)
    try:
        article.download()
        article.parse()
    except:
        return

    if article.text == None:
        return

    parsed_article = {}
    parsed_article['url'] = article.url
    parsed_article['title'] = article.title
    parsed_article['date'] = article.publish_date
    parsed_article['html'] = article.html
    parsed_article['text'] = article.text    

    return parsed_article


# @dask.delayed
def translate(article, lang):

    if lang == "en":
        article['translated_title'] = article["title"]
        return article

    translator = Translator()

    try:
        article['translated_title'] = translator.translate(
            article["title"], src=lang).text
        # print("\n\nTRANSLATED!\n\n")
    except:
        article['translated_title'] = "ERROR"

    return article


def write_parsed(parsed, filename):
    try:
        parsed.to_pickle(filename)
        print(f"\n\nSaved articles to {filename}\n")
    except Exception as e:
        print(e)
        print(f"\n\nFailed to write file. Continuing...\n")


def parse_article(row):
   
    url = row["article_links"]
    name = row["name"]
    lang = row["lang_short"]
    tld = row["top_level_domain"]

    parsed_article = get_article(url) #[get_article(url, lang) for url in urls]
    if parsed_article:
        parsed_article = parse_html(parsed_article)#[parse_html(pa) for pa in parsed_articles]
        # parsed_article = translate(parsed_article, lang)#[translate(pa, lang) for pa in parsed_articles]
        
    row['parsed_article'] = parsed_article

    return row

def launch_dask(urlfile):

    date_string = urlfile.split('/')[-1].split('_')[0]
    part = urlfile.split('_')[-1].split('.')[0]
    try:
        print(f"\n\nParsing {date_string} part {int(part)+1}/10 ...")
    except:
        print(f"\n\nParsing {date_string} ...")

    pruned = pd.read_pickle(urlfile)
    pruned['parsed_article'] = [{}]*len(pruned)
    ddf = dd.from_pandas(pruned, npartitions=10)
    parsed = ddf.apply(parse_article, axis=1, result_type='expand', meta=pruned)

    return parsed
  
        
def main(args):
    urlfile = args.url_file

    date_string = urlfile.split('/')[-1].split('.')[0]
    filename = f"{cwd()}/parsed/{date_string}_parsed.pkl"

    if os.path.exists(filename):
        sprint(f"Parsed file already exists at {filename}! Continuing...")
        return
    
    if not os.path.exists(f"{cwd()}/parsed"):
        os.mkdir(f"{cwd()}/parsed")
    
    parsed = launch_dask(urlfile)
    
    if args.visualize:
        parsed.visualize(
            filename=f"parse_articles_graph_{date_string}.svg")
    else:
        parsed = parsed.compute()
        write_parsed(parsed, filename)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--visualize", action='store_true', required=False,
                        help="skips computation and outputs graph (requires graphviz installed)")
    parser.add_argument("--url_file", required=True, type=str,
                        help="full path of the file to be parsed")
    args = parser.parse_args()
    
    main(args)

    
    


    
        

