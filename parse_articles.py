from collections import Counter
import glob
import pandas as pd
from datetime import datetime
import os

import seaborn as sns
import matplotlib.pyplot as plt

def cwd():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def dropDups(links, threshold = len(urlfiles)*.6):
    counts = Counter(links)
    res = [k for k,v in counts.items() if v < threshold]
    return res

if __name__ == "__main__":
    urlfiles = sorted(glob.glob(f"{cwd()}/data/*urls.pkl"))
    
