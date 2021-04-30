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

Move into the newly created 'newsnet' directory using the command:

`cd newsnet`

Using the following command, install the required Python modules listed in `requirements.txt`. **Note:** this could take several minutes depending on your network connection:

`pip install -q --upgrade --user -r requirements.txt`

### Step 2. Define source list and get article URLs

The source list is a **tab separated** data file containing details about the news sources to be analysed. 

**Option 1.** Use the predefined source list extracted from the [European Media Monitor](https://emm.newsbrief.eu/NewsBrief/sourceslist/en/list.html). This list contains metadata for over 8000 news sources (with a storng skew towards European sources). If you choose to go with this options, wherever you see `<sources_file>` within a command, use `sources_emm.csv` instead and proceed to [Step 3](#-step-3)

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

Once you have the source list, 

## Methodology

