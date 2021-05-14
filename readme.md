# Table of Contents 
- [NewsNet](#newsnet)
  * [Background](#background)
  * [Getting Started](#getting-started)
    + [Step 0. Install Prerequisites](#step-0-install-prerequisites)
    + [Step 1. Clone the NewsNet repository and install requirements](#step-1-clone-the-newsnet-repository-and-install-requirements)
    + [Step 2. Define source list and get article URLs](#step-2-define-source-list-and-get-article-urls)
  * [Methodology](#methodology)

# NewsNet

NewsNet is a set of tools designed to mine, process, and analyse the link network of global news sources.



## Background

NewsNet is comprised of three broad steps:

1. Collect URLs for news articles from the [GDELT FrontPage Graph database](https://blog.gdeltproject.org/announcing-gdelt-global-frontpage-graph-gfg/)
2. Download and parse HTML content from collected URLs
3. Produce a graph representation of the links between news sources

See the [Methodology](#-methodology) section for more details.

## Getting Started

This section provides an outline of how to get started with NewsNet.

### Step 0. Install Prerequisites

Ensure you have a working installation of Python3. The following links may be useful:

* [Check if Python3 is installed](https://phoenixnap.com/kb/check-python-version)
* [Installing Python3](https://realpython.com/installing-python/)

Ensure you have a working installation of Git. This will make getting setup much easier:

* [Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

Optional - set up a virtual environment! This is always a good idea as it keeps your local Python installation pristine:

* [Creating virtual environments using `venv`](https://docs.python.org/3/library/venv.html)

### Step 1. Clone the NewsNet repository and install requirements

Open a Terminal window, navigate to an approriate directory, and run the following command on your machine to clone the NewsNet repository:

`git clone https://github.com/maddran/newsnet`

Move into the newly created `newsnet` directory using the command:

`cd newsnet`

Using the following command, install the required Python modules listed in `requirements.txt`. **Note:** this could take several minutes depending on your network connection:

`pip install --upgrade --user -r requirements.txt --quiet && cd ..`

### Step 2. Define source list and get article URLs

The source list is a **tab separated** data file containing details about the news sources to be analysed. 

**Option 1.** Use the predefined source list extracted from the [European Media Monitor](https://emm.newsbrief.eu/NewsBrief/sourceslist/en/list.html). This list contains metadata for over 8000 news sources (with a storng skew towards European sources). If you choose to go with this options, wherever you see `<SOURCE_FILE>` within a command, use `newsnet\sources_emm.tsv` instead and proceed to [Step 3](#-step-3)

**Option 2.** Define your own list of sources following the description provided below. Please ensure the list is presented in a **[tab separated file](https://en.wikipedia.org/wiki/Tab-separated_values)** to ensure no conflicts arise when parsing source metadata.

The source list must contain the following columns, named *exactly* as shown:

* `category` - defines the scope of the news source providing high level aggregation (e.g. Local, National, International)
* `country` - full country name (e.g. Canada, Finland, United Kingdom)
* `country_short` - two letter country code (e.g. CA, FI, UK)
* `lang` - language of sources (e.g. French, Finnish, English)
* `lang_short`- [two letter language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
* `name` - short name used to identify the source (e.g. nytimes, yle-finnish, bbc-sports)
* `region` - high level regional aggregation (e.g. Africa, South Asia, Europe)
* `subject` - topic of news source (e.g. General News, Sports, Business, Economy)
* `text` - full name of source (e.g. The New York Times, YLE News Finnish, BBC Sports)
* `type` - type of news sources (e.g. blog, newspaper, tv, radio)
* `url` - the URL of the source (this URL must contain article links for the parsing step to work)

Once you have the source list,run the following command to download URLs from GDELT:

`python3 newsnet\get_article_urls.py --source_file <SOURCE_FILE> --start_date <START_DATE> --num_days <NUM_DAYS> --time_of_day <TIME_OF_DAY> --distribute`

Where the arguments are defined as follows:

* `<SOURCE_FILE>` - full file path of the tab separated source list file (either predefined or user generated)
* `<START_DATE>` - the date of the first day in the period you wish to analyse. Must in the form `YYYYMMDD` - e.g. September 1, 2020 would be `20200901`
* `<TIME_OF_DAY>` - defines the time of day to use when downloading GDELT FrontPage graph scrape. Formatted as an integer - e.g. 9am would be `9` and 11pm would be `23`. Defaults to `9`.
* `distribute` - flag attempts to parallelize the downloading and preperation of data. If you choose to use this flag please ensure you have **at least 3GB of RAM for each core** on your machine. i.e. 2 core system should have >= 6GB RAM,  4 core system should have >= 12GB RAM.

**N.B.** If you are using the predefined source list, each day of GDELT data will take approximately 15 mins to collect.

To wrap up this step, if you wanted to analyse the link network for the predefined (EMM) source list for the time period of March 1, 2021 to March 10, 2021 (10 days), using the GDELT data scraped at noon each day, you would run the following command:

`python3 newsnet/get_article_urls.py --source_file newsnet\sources_emm.csv --start_date 20210301 --num_days 10 --time_of_day 12 --distribute`

Once the URLs have been downloaded and processed, we are left with a directory `data` with the following structure:

```
data
|__ raw_urls
|   |   <RAW_URL_FILE_1>
|   |   <RAW_URL_FILE_2>
|   |        ...
|   |   <RAW_URL_FILE_N>
|__ pruned_urls
|   |   <PRUNED_URL_FILE_1>
|   |   <PRUNED_URL_FILE_2>
|   |        ...
|   |   <PRUNED_URL_FILE_N>
```

Where each:
* `<RAW_URL_FILE_N>` is the GDELT URLs for each day filtered to include on the sources present in the defined source list.
* `<PRUNED_URL_FILE_N>` is the corresponding `<RAW_URL_FILE_N>` with any recurring URLs pruned out. These files contain the final list of article URLs that will be processed and parsed.

### Step 3. Parse Articles

Now that we have the pruned URLs for each day in the analysis period, we can move on to processing and parsing the news articles at those URLs. This step involves rendering the HTML for each URL and parsing the page for data such as:

* Article publish date
* Article HTML
* Article Headline
* Article Text
* Article Author
* Embedded Links (internal and external)

To parse news articles, we run the following script for each pruned URL file (denoted as `<PRUNED_URL_FILE>` below):

`python3 newsnet/parse_articles.py --url_file <PRUNED_URL_FILE>`

Assuming the file structure presented previously, we can call the above script in a loop as follows:

`for FILE in data/pruned_urls/*; do python3 newsnet/parse_articles.py --url_file $FILE; done`

Once the articles have been parsed, we are left with a directory `parsed` with the following structure:

```
parsed
|   <PARSED_ARTICLES_FILE_1>
|   <PARSED_ARTICLES_FILE_2>
|           ...
|   <PARSED_ARTICLES_FILE_N>
```
Each `<PARSED_ARTICLES_FILE_N>` is a pickle file containing a dataframe where each row represents one parsed news article.

## Parallelizing on SLURM cluster

## Methodology

