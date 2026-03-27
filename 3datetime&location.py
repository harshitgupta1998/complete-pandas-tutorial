df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
df = df.dropna(subset=["timestamp"])
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["weekday"] = df["timestamp"].dt.day_name()

daily = df.set_index("timestamp").resample("D").size().reset_index(name="count")
by_type = df.groupby("type").size().reset_index(name="count")
hourly_type = df.groupby([pd.Grouper(key="timestamp", freq="H"), "type"]).size().reset_index(name="count")

df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]


filtered = df.copy()

filtered = filtered[
    (filtered["timestamp"] >= pd.to_datetime(start_date)) &
    (filtered["timestamp"] <= pd.to_datetime(end_date))
]

if selected_types:
    filtered = filtered[filtered["type"].isin(selected_types)]

## Time Summary ###
Here is a clean Python prep template for the bonus spatial/temporal reasoning part.

Assume your data looks like this:

import pandas as pd

# Example columns:
# timestamp, region, incident_type, lat, lon
df = pd.read_csv("incidents.csv")

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date
df["weekday"] = df["timestamp"].dt.day_name()
df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5
1. Morning vs afternoon by region

Question: Which region saw the largest increase between morning and afternoon?

df["time_window"] = df["hour"].apply(
    lambda h: "morning" if 6 <= h < 12 else "afternoon" if 12 <= h < 18 else "other"
)

temp = df[df["time_window"].isin(["morning", "afternoon"])]

counts = (
    temp.groupby(["region", "time_window"])
    .size()
    .unstack(fill_value=0)
)

counts["increase"] = counts["afternoon"] - counts["morning"]

largest_increase = counts.sort_values("increase", ascending=False)
print(largest_increase.head())
2. Hourly spikes

Question: Which type peaks at what hour?

hourly_type = (
    df.groupby(["incident_type", "hour"])
    .size()
    .reset_index(name="count")
)

peak_hour_by_type = hourly_type.loc[
    hourly_type.groupby("incident_type")["count"].idxmax()
].sort_values("count", ascending=False)

print(peak_hour_by_type)
3. Rolling average over time

Useful for smoothing noisy time series.

hourly_counts = (
    df.set_index("timestamp")
    .resample("1H")
    .size()
    .rename("count")
    .reset_index()
)

hourly_counts["rolling_3h"] = hourly_counts["count"].rolling(3).mean()

print(hourly_counts.head(10))
4. Cumulative growth

Shows how incidents build over the day or week.

hourly_counts["cumulative"] = hourly_counts["count"].cumsum()
print(hourly_counts.tail())

If per region:

region_hourly = (
    df.groupby(["region", pd.Grouper(key="timestamp", freq="1H")])
    .size()
    .reset_index(name="count")
    .sort_values(["region", "timestamp"])
)

region_hourly["cumulative"] = region_hourly.groupby("region")["count"].cumsum()
print(region_hourly.head(10))
5. Counts by region

Basic spatial comparison

region_counts = df["region"].value_counts().reset_index()
region_counts.columns = ["region", "count"]
print(region_counts)

### Location Summary ###

6. Change by location across time windows

Question: Which region increased the most from early to late window?

df["window"] = df["hour"].apply(
    lambda h: "early" if h < 12 else "late"
)

region_window = (
    df.groupby(["region", "window"])
    .size()
    .unstack(fill_value=0)
)

region_window["diff"] = region_window["late"] - region_window["early"]
print(region_window.sort_values("diff", ascending=False))
7. Weekday vs weekend
weekday_weekend = (
    df.groupby(["region", "is_weekend"])
    .size()
    .unstack(fill_value=0)
)

weekday_weekend.columns = ["weekday", "weekend"]
weekday_weekend["weekend_minus_weekday"] = (
    weekday_weekend["weekend"] - weekday_weekend["weekday"]
)

print(weekday_weekend.sort_values("weekend_minus_weekday", ascending=False))
8. Top incident type by region

Question: What type dominates each region?**

region_type = (
    df.groupby(["region", "incident_type"])
    .size()
    .reset_index(name="count")
)

top_type_by_region = region_type.loc[
    region_type.groupby("region")["count"].idxmax()
].sort_values("count", ascending=False)

print(top_type_by_region)
9. Top type by region over time

Combined spatial + temporal

df["hour_bucket"] = df["timestamp"].dt.floor("1H")

region_type_time = (
    df.groupby(["region", "hour_bucket", "incident_type"])
    .size()
    .reset_index(name="count")
)

top_type_each_region_hour = region_type_time.loc[
    region_type_time.groupby(["region", "hour_bucket"])["count"].idxmax()
]

print(top_type_each_region_hour.head(20))
10. Detect outliers in time

Simple Z-score style approach for hourly counts.

hourly_counts = (
    df.set_index("timestamp")
    .resample("1H")
    .size()
    .rename("count")
    .reset_index()
)

mean = hourly_counts["count"].mean()
std = hourly_counts["count"].std()

hourly_counts["zscore"] = (hourly_counts["count"] - mean) / std
outliers = hourly_counts[hourly_counts["zscore"] > 2]

print(outliers)
11. Detect densest area

If you have latitude and longitude, this is a quick practical way without heavy GIS.

# Create rough spatial bins
df["lat_bin"] = df["lat"].round(2)
df["lon_bin"] = df["lon"].round(2)

density = (
    df.groupby(["lat_bin", "lon_bin"])
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

print(density.head(10))

This is often enough in an interview if they want a heatmap-like summary quickly.

12. Spread or movement pattern across geography

A simple way: compare dominant area in early vs later hours.

df["phase"] = df["hour"].apply(lambda h: "early" if h < 12 else "late")

spread = (
    df.groupby(["phase", "lat_bin", "lon_bin"])
    .size()
    .reset_index(name="count")
)

top_early = spread[spread["phase"] == "early"].sort_values("count", ascending=False).head(10)
top_late = spread[spread["phase"] == "late"].sort_values("count", ascending=False).head(10)

print("Early hotspots")
print(top_early)

print("\nLate hotspots")
print(top_late)

If hotspot bins shift, you can describe it as a movement/spread pattern.

13. Nearest points

If they ask for nearby incidents, use haversine or sklearn.

from sklearn.neighbors import BallTree
import numpy as np

coords = df[["lat", "lon"]].dropna().copy()
coords_rad = np.radians(coords)

tree = BallTree(coords_rad, metric="haversine")

# Query nearest neighbors for first point
dist, ind = tree.query(coords_rad.iloc[[0]], k=5)

# Convert radians to km
earth_radius_km = 6371
print(dist[0] * earth_radius_km)
print(ind[0])
14. Simple plots you should know
Hourly line chart
import matplotlib.pyplot as plt

hourly = df.groupby("hour").size()

plt.figure(figsize=(8,4))
hourly.plot(kind="line", marker="o")
plt.title("Incidents by Hour")
plt.xlabel("Hour")
plt.ylabel("Count")
plt.grid(True)
plt.show()
Region bar chart
region_counts = df["region"].value_counts()

plt.figure(figsize=(8,4))
region_counts.plot(kind="bar")
plt.title("Incidents by Region")
plt.xlabel("Region")
plt.ylabel("Count")
plt.show()
Pivot heatmap-like table
pivot = df.pivot_table(
    index="region",
    columns="hour",
    values="incident_type",
    aggfunc="count",
    fill_value=0
)

print(pivot)

df["timestamp_local"] = df["timestamp_utc"].dt.tz_convert("America/Los_Angeles")

###
A very strong dashboard layout
Top row
  total events
  unique types
  active regions
  selected date range
Left sidebar
  date range
  type multiselect
  region selector
  aggregation granularity
Main section
  Map
  points or heatmap
  tooltip: time, type, location
Time series
  events over time
  optionally split by type
  Category breakdown
  bar chart by type
Region summary
  table or bar chart of top regions
