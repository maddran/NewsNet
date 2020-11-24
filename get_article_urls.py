import pandas as pd
from sqlalchemy import *
import requests
from datetime import datetime, timedelta
import gzip
import shutil
import os
from tqdm import tqdm


def get_GDELT_data(date):
  date_string = date.strftime("%Y%m%d%H%M%S")
  url = f"http://data.gdeltproject.org/gdeltv3/gfg/alpha/{date_string}.LINKS.TXT.gz"

  filename = url.split("/")[-1]
  with open(filename, "wb") as f:
      r = requests.get(url)
      f.write(r.content)
      
  fileout = filename.split(".")[0] + ".txt"

  with gzip.open(filename, 'rb') as f_in:
      with open(fileout, 'wb') as f_out:
          shutil.copyfileobj(f_in, f_out)

  os.remove(filename)

  return fileout

def populate_sql(file):

  j = 1
  chunksize = 10000
  db_file = f"{file.split('.')[0]}.db"
  
  if os.path.exists(db_file):
    os.remove(db_file)

  db_path = f"sqlite:///{db_file}"
  urls_database = create_engine(db_path)

  for df in tqdm(pd.read_csv(file, chunksize=chunksize, iterator=True, 
                        sep='\t', header=None, error_bad_lines = False), total = 1000):
    df.columns = ['Date', 'FrontPageURL', 'LinkID', 'LinkPerc', 'LinkURL', 'LinkText']  
    df.index += j
    df.to_sql("urls_table", urls_database, if_exists='append')
    j = df.index[-1] + 1

    # if j>100e6:
    #   print(f"****BREAKING at {j} lines read! Remove in production!****")
    #   break

  urls_database.execute("CREATE INDEX urls_index ON urls_table(FrontPageURL)")
    
  os.remove(file)
  return (db_path, j)