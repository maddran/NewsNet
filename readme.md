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

Move into the newly created 'newsnet' directory:

`cd newsnet`

Install the required modules listed in `requirements.txt`. **Note:** this could take several minutes depending on your network connection:

`pip install -q --upgrade --user -r requirements.txt`

### Step 2. Define source list and get article URLs



## Methodology