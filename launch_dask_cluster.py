from dask.distributed import Client
from dask_jobqueue import SLURMCluster
from get_article_urls import urls_main
import os

def main(args):
    cluster = SLURMCluster(
        cores=40,
        processes=20,
        memory="10GB",
        queue="large",
        walltime="02:00:00",
        local_directory='/tmp',
        interface="ib0",
        project= args.project)

    client = Client(cluster)
    cluster.adapt(minimum_jobs = 40, maximum_memory = "300GB")

    urls_main(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=str,
                        help="The project to bill computation to. String of the form (project_200xxxx)")
    parser.add_argument("--start_date", required=True, type=int,
                        help="the start date of the period to collect (yyyymmdd)")
    parser.add_argument("--num_days", required=True, type=int,
                        help="num days from start date to collect")
    parser.add_argument("--time_of_day", required=False, type=int, default=9,
                        help="time of day to collect links (only whole hours in 24h format)")
    parser.add_argument("--distribute", action='store_true',
                        help="starts local cluster")
    parser.add_argument("--visualize", action='store_true',
                        help="skips computation and outputs graph (requires graphviz installed)")
    args = parser.parse_args()

    main(args)
