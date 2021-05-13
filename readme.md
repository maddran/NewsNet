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

`pip install -q --upgrade --user -r requirements.txt && cd ..`

### Step 2. Define source list and get article URLs

The source list is a **tab separated** data file containing details about the news sources to be analysed. 

**Option 1.** Use the predefined source list extracted from the [European Media Monitor](https://emm.newsbrief.eu/NewsBrief/sourceslist/en/list.html). This list contains metadata for over 8000 news sources (with a storng skew towards European sources). If you choose to go with this options, wherever you see `<SOURCE_FILE>` within a command, use `newsnet\sources_emm.csv` instead and proceed to [Step 3](#-step-3)

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

* `<START_DATE>` - the date of the first day in the period you wish to analyse. Must in the form `YYYYMMDD` - e.g. September 1, 2020 would be `20200901`
* `<TIME_OF_DAY>` - defines the time of day to use when downloading GDELT FrontPage graph scrape. In 4 digit 24h format - e.g. 9am would be `0900` and 11pm would be `2300`. Defaults to `0900`.
* `distribute` - flag attempts to parallelize the downloading and preperation of data. If you choose to use this flag please ensure you have **at least** 3GB of RAM for each core on your machine. i.e. 2 core system should have >= 6GB RAM,  4 core system should have >= 12GB RAM.

**N.B.** If you are using the predefined source list, each day of GDELT data will take approximately 15 mins to collect.

If you wanted to analyse the link network for the predefined (EMM) source list for the time period of March 1, 2021 to March 10, 2021 (10 days), using the GDELT data scraped at noon each day, you would run the following command:

`python3 newsnet\get_article_urls.py --source_file newsnet\sources_emm.csv --start_date 20210301 --num_days 10 --time_of_day 1200 --distribute`

## Methodology

