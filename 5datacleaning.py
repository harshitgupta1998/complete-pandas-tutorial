lean bad timestamps / nulls / malformed geo fields
aggregate by time and category/type
Thought for a couple of seconds

Use this pattern.

1. Clean bad timestamps, nulls, malformed geo
import pandas as pd
import numpy as np

df = pd.read_csv("incidents.csv")

# standardize column names
df.columns = df.columns.str.strip().str.lower()

# parse timestamp safely
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# convert geo fields safely
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

# optional: strip and clean category/type
df["incident_type"] = df["incident_type"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})

# remove bad timestamps
df = df.dropna(subset=["timestamp"])

# remove bad geo rows
df = df.dropna(subset=["lat", "lon"])

# remove impossible coordinates
df = df[(df["lat"].between(-90, 90)) & (df["lon"].between(-180, 180))]

# remove rows with missing type if needed
df = df.dropna(subset=["incident_type"])

# sort by time
df = df.sort_values("timestamp").reset_index(drop=True)

print(df.head())
print(df.shape)
2. Create useful time columns
df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date
df["day"] = df["timestamp"].dt.day_name()
df["hour_bucket"] = df["timestamp"].dt.floor("1H")
3. Aggregate by time
incidents per hour
hourly_counts = (
    df.groupby("hour_bucket")
      .size()
      .reset_index(name="count")
)

print(hourly_counts.head())
incidents per day
daily_counts = (
    df.groupby("date")
      .size()
      .reset_index(name="count")
)

print(daily_counts.head())
4. Aggregate by category/type
type_counts = (
    df.groupby("incident_type")
      .size()
      .reset_index(name="count")
      .sort_values("count", ascending=False)
)

print(type_counts)
5. Aggregate by time and category/type together
type count by hour
hour_type_counts = (
    df.groupby(["hour_bucket", "incident_type"])
      .size()
      .reset_index(name="count")
      .sort_values(["hour_bucket", "count"], ascending=[True, False])
)

print(hour_type_counts.head(20))
pivot table for dashboard
pivot_hour_type = df.pivot_table(
    index="hour_bucket",
    columns="incident_type",
    values="lat",          # any column works if using count
    aggfunc="count",
    fill_value=0
)

print(pivot_hour_type.head())
6. Very common interview version
import pandas as pd
import numpy as np

df = pd.read_csv("incidents.csv")
df.columns = df.columns.str.strip().str.lower()

# clean
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df["incident_type"] = df["incident_type"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})

df = df.dropna(subset=["timestamp", "lat", "lon", "incident_type"])
df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]
df = df.sort_values("timestamp")

# time features
df["hour_bucket"] = df["timestamp"].dt.floor("1H")
df["day"] = df["timestamp"].dt.date

# aggregations
hourly = df.groupby("hour_bucket").size().reset_index(name="count")
by_type = df.groupby("incident_type").size().reset_index(name="count").sort_values("count", ascending=False)
hour_type = df.groupby(["hour_bucket", "incident_type"]).size().reset_index(name="count")

print("Hourly counts")
print(hourly.head())

print("\nCounts by type")
print(by_type)

print("\nHourly by type")
print(hour_type.head(20))
