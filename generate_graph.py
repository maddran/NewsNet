import pandas as pd
import argparse
import os, sys

def get_links(file):
    df = pd.read_pickle(file)
    df = df[df['parsed_article'].notna()]
    df_articles = pd.DataFrame(df['parsed_article'].values.tolist(), index = df.index)
    df_res = pd.concat([df.loc[:,['index', 'top_level_domain']],
                        df_articles.loc[:,['internal_links', 'parsed_date']]])
    print(df_res.isna().sum()/len(df_res))
    # print(df.explode('enternal_links').head(5))

def get_source_tld():
    pass


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_files", required=True, type=lambda x: is_valid_file(parser, x),
                        nargs='+', help="full path of the parsed files to generate a network from")

    args = parser.parse_args()

    _ = [get_links(file) for file in args.url_files] 
