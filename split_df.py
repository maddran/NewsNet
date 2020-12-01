import pandas as pd
import numpy as np

def split_file(url_file, n):
    df = pd.read_pickle(url_file)
    df = df.explode('article_links').reset_index(drop=False)
    splits = np.array_split(df, n)
    url_files =[]
    for i, s in enumerate(splits):
        filepath = f"{url_file.split('.')[0]}_{i}.pkl"
        s.to_pickle(filepath)
        url_files.append(filepath)


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=str,
                        help="The project to bill computation to. String of the form (project_200xxxx)")
    parser.add_argument("--url_file", required=True, type=lambda x: is_valid_file(parser, x),
