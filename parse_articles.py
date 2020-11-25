from collections import Counter
import glob
import pandas as pd
from datetime import datetime

import seaborn as sns
import matplotlib.pyplot as plt

urlfiles = sorted(glob.glob("/content/drive/My Drive/NewsNet/URLs/*.pkl"))

def dropDups(links, threshold = len(urlfiles)*.6):
  counts = Counter(links)
  res = [k for k,v in counts.items() if v < threshold]
  return res