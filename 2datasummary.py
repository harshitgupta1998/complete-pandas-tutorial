import pandas as pd

df = pd.read_csv("data.csv")

print(df.shape)
print(df.columns.tolist())
print(df.head(3))
print(df.dtypes)
print(df.isna().sum().sort_values(ascending=False))


import requests
import json

r = requests.get(url, timeout=10)
data = r.json()

print(type(data))
print(data if isinstance(data, dict) else data[:2])
