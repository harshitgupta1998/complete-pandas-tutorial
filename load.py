import pandas as pd
DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
         'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

def load_data(nrows=100):
    data=pd.read_csv(DATA_URL,nrows=nrows)
    lowercase=lambda x: str(x).lower()
    data.rename(lowercase,axis='columns',inplace=True)
    data[DATE_COLUMN]=pd.to_datetime(data[DATE_COLUMN])
    return data
