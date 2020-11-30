from dask.distributed import Client
from dask_jobqueue import SLURMCluster
import pandas as pd
import numpy as np
import argparse
import os, sys

from parse_articles import main as parse_main

def update_args(args, file):
    d = vars(args)
    d['url_file'] = file

def split_file(url_file):
    df = pd.read_pickle(url_file)
    df = df.explode('article_links').reset_index(drop=False)
    splits = np.array_split(df, 4)
    url_files =[]
    for i, s in enumerate(splits):
        filepath = f"{url_file.split('.')[0]}_{i}.pkl"
        s.to_pickle(filepath)
        url_files.append(filepath)

    return url_files

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

def run_parse(args, file):
    update_args(args, file)
    parse_main(args)
    


def main(args):

    split_files = split_file(args.url_file)


    if args.distribute:
        extra_args = [
            "-J newsnet_worker"
            "--mail-type=ALL",
            "--mail-user=madhav.narendran@helsinki.fi"
            "--gres=nvme:100"]

        cluster = SLURMCluster(
            name = "newsnet_worker",
            cores = 20,
            memory="2GB",
            queue="small",
            walltime="3:00:00",
            local_directory = '/tmp',
            log_directory = f"{os.environ.get('PWD')}/dask-worker-space",
            project = args.project,
            job_extra = extra_args)

        with Client(cluster) as client:
            print("\n\nLaunching Dask SLURM cluster...")
            cluster.scale(4)
            client.upload_file(
                f'{os.path.dirname(os.path.abspath(sys.argv[0]))}/parse_articles.py')
            print(client.run(os.getcwd))
            _ = [run_parse(args, file) for file in split_files]
            [os.remove(sf) for sf in split_files]
    else:
        with Client() as client:
            _ = [run_parse(args, file) for file in split_files]
            [os.remove(sf) for sf in split_files]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=str,
                        help="The project to bill computation to. String of the form (project_200xxxx)")
    parser.add_argument("--url_file", required=True, type=lambda x: is_valid_file(parser, x),
                        help="full path of the url file to be parsed")
    parser.add_argument("--distribute", action='store_true',
                        help="starts local cluster")
    parser.add_argument("--visualize", action='store_true',
                        help="skips computation and outputs graph (requires graphviz installed)")
    args = parser.parse_args()

    main(args)
