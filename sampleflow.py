import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Incident Dashboard", layout="wide")

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("incidents.csv")
    df.columns = df.columns.str.strip().str.lower()

    # Clean timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Clean geo
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # Clean text/category fields
    if "incident_type" in df.columns:
        df["incident_type"] = (
            df["incident_type"]
            .astype(str)
            .str.strip()
            .replace({"": np.nan, "nan": np.nan, "None": np.nan})
        )

    if "region" in df.columns:
        df["region"] = (
            df["region"]
            .astype(str)
            .str.strip()
            .replace({"": np.nan, "nan": np.nan, "None": np.nan})
        )

    # Drop bad rows
    required_cols = ["timestamp", "lat", "lon"]
    for col in required_cols:
        if col in df.columns:
            df = df[df[col].notna()]

    # Filter impossible coordinates
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]

    # Time features
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day_name"] = df["timestamp"].dt.day_name()
    df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5
    df["hour_bucket"] = df["timestamp"].dt.floor("1H")

    df["time_window"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 17, 23],
        labels=["Night", "Morning", "Afternoon", "Evening"]
    )

    return df.sort_values("timestamp").reset_index(drop=True)


df = load_data()

st.title("Spatial / Temporal Incident Dashboard")

if df.empty:
    st.warning("No valid data after cleaning.")
    st.stop()

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) != 2:
    st.stop()

start_date, end_date = date_range

type_options = sorted(df["incident_type"].dropna().unique()) if "incident_type" in df.columns else []
region_options = sorted(df["region"].dropna().unique()) if "region" in df.columns else []

selected_types = st.sidebar.multiselect(
    "Incident type",
    options=type_options,
    default=type_options
)

selected_regions = st.sidebar.multiselect(
    "Region",
    options=region_options,
    default=region_options
)

selected_hours = st.sidebar.slider(
    "Hour of day",
    min_value=0,
    max_value=23,
    value=(0, 23)
)

weekend_filter = st.sidebar.selectbox(
    "Day type",
    ["All", "Weekday", "Weekend"]
)

# -----------------------------
# Apply filters
# -----------------------------
filtered = df.copy()

filtered = filtered[
    (filtered["timestamp"].dt.date >= start_date) &
    (filtered["timestamp"].dt.date <= end_date)
]

filtered = filtered[
    filtered["hour"].between(selected_hours[0], selected_hours[1])
]

if "incident_type" in filtered.columns and selected_types:
    filtered = filtered[filtered["incident_type"].isin(selected_types)]

if "region" in filtered.columns and selected_regions:
    filtered = filtered[filtered["region"].isin(selected_regions)]

if weekend_filter == "Weekday":
    filtered = filtered[filtered["is_weekend"] == False]
elif weekend_filter == "Weekend":
    filtered = filtered[filtered["is_weekend"] == True]

if filtered.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

# -----------------------------
# KPI row
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total incidents", len(filtered))
c2.metric("Unique regions", filtered["region"].nunique() if "region" in filtered.columns else "N/A")
c3.metric("Unique types", filtered["incident_type"].nunique() if "incident_type" in filtered.columns else "N/A")
c4.metric("Date span", f"{filtered['date'].min()} → {filtered['date'].max()}")

# -----------------------------
# Aggregations
# -----------------------------
hourly_counts = (
    filtered.groupby("hour_bucket")
    .size()
    .reset_index(name="count")
)

type_counts = (
    filtered.groupby("incident_type")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    if "incident_type" in filtered.columns else pd.DataFrame()
)

region_counts = (
    filtered.groupby("region")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    if "region" in filtered.columns else pd.DataFrame()
)

hour_type_counts = (
    filtered.groupby(["hour_bucket", "incident_type"])
    .size()
    .reset_index(name="count")
    if "incident_type" in filtered.columns else pd.DataFrame()
)

# Spatial binning for density-style map
filtered["lat_bin"] = filtered["lat"].round(2)
filtered["lon_bin"] = filtered["lon"].round(2)

density = (
    filtered.groupby(["lat_bin", "lon_bin"])
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

# -----------------------------
# Map
# -----------------------------
st.subheader("Map")

map_mode = st.radio(
    "Map view",
    ["Raw points", "Density bins"],
    horizontal=True
)

if map_mode == "Raw points":
    hover_cols = ["timestamp", "lat", "lon"]
    if "incident_type" in filtered.columns:
        hover_cols.append("incident_type")
    if "region" in filtered.columns:
        hover_cols.append("region")

    fig_map = px.scatter_map(
        filtered,
        lat="lat",
        lon="lon",
        color="incident_type" if "incident_type" in filtered.columns else None,
        hover_data=hover_cols,
        zoom=3,
        height=500
    )
    st.plotly_chart(fig_map, use_container_width=True)

else:
    fig_density = px.scatter_map(
        density,
        lat="lat_bin",
        lon="lon_bin",
        size="count",
        hover_data=["count"],
        zoom=3,
        height=500
    )
    st.plotly_chart(fig_density, use_container_width=True)

# -----------------------------
# Charts
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Incidents over time")
    fig_time = px.line(
        hourly_counts,
        x="hour_bucket",
        y="count",
        markers=True
    )
    st.plotly_chart(fig_time, use_container_width=True)

with right:
    st.subheader("Incidents by hour")
    hour_summary = (
        filtered.groupby("hour")
        .size()
        .reset_index(name="count")
    )
    fig_hour = px.bar(
        hour_summary,
        x="hour",
        y="count"
    )
    st.plotly_chart(fig_hour, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("By type")
    if not type_counts.empty:
        fig_type = px.bar(
            type_counts.head(15),
            x="incident_type",
            y="count"
        )
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("incident_type column not available")

with right2:
    st.subheader("By region")
    if not region_counts.empty:
        fig_region = px.bar(
            region_counts.head(15),
            x="region",
            y="count"
        )
        st.plotly_chart(fig_region, use_container_width=True)
    else:
        st.info("region column not available")

# -----------------------------
# Combined view
# -----------------------------
st.subheader("Type over time")

if not hour_type_counts.empty:
    fig_combo = px.line(
        hour_type_counts,
        x="hour_bucket",
        y="count",
        color="incident_type",
        markers=False
    )
    st.plotly_chart(fig_combo, use_container_width=True)
else:
    st.info("incident_type column not available")

# -----------------------------
# Interactive exploration table
# -----------------------------
st.subheader("Explore filtered data")

show_cols = [c for c in [
    "timestamp", "region", "incident_type", "lat", "lon",
    "hour", "day_name", "time_window", "is_weekend"
] if c in filtered.columns]

st.dataframe(
    filtered[show_cols],
    use_container_width=True,
    height=350
)

# -----------------------------
# Quick insights
# -----------------------------
st.subheader("Quick insights")

insight_lines = []

if "region" in filtered.columns and not region_counts.empty:
    top_region = region_counts.iloc[0]
    insight_lines.append(f"Top region: **{top_region['region']}** with **{top_region['count']}** incidents.")

if "incident_type" in filtered.columns and not type_counts.empty:
    top_type = type_counts.iloc[0]
    insight_lines.append(f"Top type: **{top_type['incident_type']}** with **{top_type['count']}** incidents.")

top_hour_row = (
    filtered.groupby("hour")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    .iloc[0]
)
insight_lines.append(f"Peak hour: **{int(top_hour_row['hour'])}:00** with **{int(top_hour_row['count'])}** incidents.")

for line in insight_lines:
    st.markdown(f"- {line}")
