import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np

# ── Step 1: Fetch & Parse Data ───────────────────────────────

st.set_page_config(page_title="🌍 Earthquake Dashboard", layout="wide")
st.title("🌍 Earthquake Intelligence Dashboard")

@st.cache_data(ttl=600)
def fetch_data():
    """Fetch earthquake data from USGS API."""
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": "2025-03-01",
        "endtime": "2025-03-27",
        "minmagnitude": 2.5,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def parse_to_df(geojson):
    """Parse GeoJSON into a clean DataFrame."""
    rows = []
    for f in geojson.get("features", []):
        p = f["properties"]
        c = f["geometry"]["coordinates"]
        rows.append({
            "magnitude": p.get("mag"),
            "place": p.get("place"),
            "time": p.get("time"),
            "tsunami": p.get("tsunami", 0),
            "longitude": c[0],
            "latitude": c[1],
            "depth_km": c[2],
        })
    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["date"] = df["datetime"].dt.date
    df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce")
    df["depth_km"] = pd.to_numeric(df["depth_km"], errors="coerce")
    df.dropna(subset=["magnitude", "latitude", "longitude"], inplace=True)
    return df

# Load data
with st.spinner("Fetching earthquake data from USGS..."):
    raw = fetch_data()
    df = parse_to_df(raw)

# ── Step 4: Sidebar Filters ─────────────────────────────────

st.sidebar.header("🔎 Filters")

# Date range
min_date = df["date"].min()
max_date = df["date"].max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Magnitude slider
mag_min = float(df["magnitude"].min())
mag_max = float(df["magnitude"].max())
mag_range = st.sidebar.slider(
    "Magnitude Range",
    min_value=mag_min, max_value=mag_max,
    value=(mag_min, mag_max), step=0.1,
)

# Depth slider
depth_min = int(df["depth_km"].min())
depth_max = int(df["depth_km"].max()) + 1
depth_range = st.sidebar.slider(
    "Depth (km)",
    min_value=depth_min, max_value=depth_max,
    value=(depth_min, depth_max), step=10,
)

# Region text filter
region_filter = st.sidebar.text_input("Search region (e.g. Alaska, Japan)")

# Tsunami only toggle
tsunami_only = st.sidebar.checkbox("🌊 Tsunami alerts only")

# Apply filters
df_filtered = df.copy()

if len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered["date"] >= date_range[0]) & (df_filtered["date"] <= date_range[1])
    ]

df_filtered = df_filtered[
    (df_filtered["magnitude"] >= mag_range[0]) & (df_filtered["magnitude"] <= mag_range[1])
    & (df_filtered["depth_km"] >= depth_range[0]) & (df_filtered["depth_km"] <= depth_range[1])
]

if region_filter:
    df_filtered = df_filtered[
        df_filtered["place"].str.contains(region_filter, case=False, na=False)
    ]

if tsunami_only:
    df_filtered = df_filtered[df_filtered["tsunami"] == 1]

st.sidebar.metric("Filtered Events", len(df_filtered))

# ── Step 2: Metrics & Data Table ─────────────────────────────

st.success(f"Showing {len(df_filtered)} of {len(df)} events  •  {df['date'].min()} → {df['date'].max()}")

# KPI metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("🔢 Total Events", len(df_filtered))
col2.metric("📏 Avg Magnitude", f"{df_filtered['magnitude'].mean():.2f}" if len(df_filtered) else "N/A")

if len(df_filtered):
    max_row = df_filtered.loc[df_filtered["magnitude"].idxmax()]
    col3.metric("💥 Max Magnitude", f"{max_row['magnitude']:.1f}", delta=max_row["place"])
else:
    col3.metric("💥 Max Magnitude", "N/A")

col4.metric("🌊 Tsunami Alerts", int(df_filtered["tsunami"].sum()) if len(df_filtered) else 0)

# ── Step 3: Interactive Map ──────────────────────────────────

st.subheader("🗺️ Earthquake Map")

# Color-code by severity
def severity(mag):
    if mag < 4.0:
        return "Low (< 4.0)"
    elif mag < 5.5:
        return "Moderate (4.0–5.5)"
    return "High (> 5.5)"

df_filtered["severity"] = df_filtered["magnitude"].apply(severity)

color_map = {
    "Low (< 4.0)": "green",
    "Moderate (4.0–5.5)": "orange",
    "High (> 5.5)": "red",
}

fig_map = px.scatter_map(
    df_filtered,
    lat="latitude",
    lon="longitude",
    color="severity",
    size="magnitude",
    hover_name="place",
    hover_data={"magnitude": True, "depth_km": True, "datetime": True, "severity": False},
    color_discrete_map=color_map,
    category_orders={"severity": ["Low (< 4.0)", "Moderate (4.0–5.5)", "High (> 5.5)"]},
    map_style="carto-darkmatter",
    zoom=1,
    height=550,
    title="",
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# ── Step 5: Charts ───────────────────────────────────────────

chart_col1, chart_col2 = st.columns(2)

# 5a — Events per day (time series)
with chart_col1:
    st.subheader("📈 Events per Day")
    if len(df_filtered):
        daily = df_filtered.groupby("date").size().reset_index(name="count")
        fig_ts = px.bar(
            daily, x="date", y="count",
            color_discrete_sequence=["#636EFA"],
            labels={"date": "Date", "count": "Events"},
        )
        fig_ts.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# 5b — Magnitude distribution (histogram)
with chart_col2:
    st.subheader("📊 Magnitude Distribution")
    if len(df_filtered):
        fig_hist = px.histogram(
            df_filtered, x="magnitude", nbins=30,
            color_discrete_sequence=["#EF553B"],
            labels={"magnitude": "Magnitude", "count": "Count"},
        )
        fig_hist.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# 5c — Top 10 regions by event count
st.subheader("🏆 Top 10 Regions by Event Count")
if len(df_filtered):
    # Extract region from "123 km NNW of <Region>" format
    df_filtered["region"] = (
        df_filtered["place"]
        .str.extract(r"of\s+(.*)", expand=False)
        .fillna(df_filtered["place"])
    )
    top_regions = df_filtered["region"].value_counts().head(10).reset_index()
    top_regions.columns = ["region", "count"]
    fig_reg = px.bar(
        top_regions, x="count", y="region", orientation="h",
        color_discrete_sequence=["#00CC96"],
        labels={"count": "Events", "region": "Region"},
    )
    fig_reg.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_reg, use_container_width=True)
else:
    st.info("No data for selected filters.")

# ── Step 6: BONUS — Temporal & Spatial Analysis ──────────────

st.divider()
st.header("🧠 Bonus: Temporal & Spatial Analysis")

bonus_col1, bonus_col2 = st.columns(2)

# 6a — Heatmap: Hour of Day vs Day of Week
with bonus_col1:
    st.subheader("🕐 Activity Heatmap (Hour × Day)")
    if len(df_filtered):
        df_filtered["hour"] = df_filtered["datetime"].dt.hour
        df_filtered["day_of_week"] = df_filtered["datetime"].dt.day_name()

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heatmap_data = (
            df_filtered.groupby(["day_of_week", "hour"])
            .size()
            .reset_index(name="count")
        )
        # Pivot for heatmap
        pivot = heatmap_data.pivot(index="day_of_week", columns="hour", values="count").fillna(0)
        pivot = pivot.reindex(day_order)  # enforce day order

        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Hour (UTC)", y="Day of Week", color="Events"),
            color_continuous_scale="YlOrRd",
            aspect="auto",
        )
        fig_heat.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No data for heatmap.")

# 6b — Depth vs Magnitude scatter
with bonus_col2:
    st.subheader("🔬 Depth vs Magnitude")
    if len(df_filtered):
        fig_scatter = px.scatter(
            df_filtered, x="depth_km", y="magnitude",
            color="severity",
            color_discrete_map=color_map,
            hover_name="place",
            labels={"depth_km": "Depth (km)", "magnitude": "Magnitude"},
            opacity=0.6,
        )
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No data for scatter plot.")

# 6c — Aftershock Detection
st.subheader("⚠️ Possible Aftershocks (within 100 km & 72 hrs of M5.5+ events)")

if len(df_filtered):
    major = df_filtered[df_filtered["magnitude"] >= 5.5].copy()

    if len(major):
        def haversine_km(lat1, lon1, lat2, lon2):
            """Calculate distance between two points in km."""
            R = 6371
            lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            return R * 2 * np.arcsin(np.sqrt(a))

        aftershocks = []
        for _, mq in major.iterrows():
            window = df_filtered[
                (df_filtered["datetime"] > mq["datetime"])
                & (df_filtered["datetime"] <= mq["datetime"] + pd.Timedelta(hours=72))
                & (df_filtered["magnitude"] < mq["magnitude"])
            ]
            for _, eq in window.iterrows():
                dist = haversine_km(mq["latitude"], mq["longitude"], eq["latitude"], eq["longitude"])
                if dist <= 100:
                    aftershocks.append({
                        "main_event": mq["place"],
                        "main_mag": mq["magnitude"],
                        "aftershock": eq["place"],
                        "aftershock_mag": eq["magnitude"],
                        "distance_km": round(dist, 1),
                        "hours_after": round((eq["datetime"] - mq["datetime"]).total_seconds() / 3600, 1),
                    })

        if aftershocks:
            af_df = pd.DataFrame(aftershocks)
            st.dataframe(af_df, use_container_width=True)
            st.caption(f"Found {len(af_df)} possible aftershocks from {len(major)} major events.")
        else:
            st.success("No aftershocks detected within 100 km / 72 hrs window.")
    else:
        st.info("No M5.5+ events in current filter to check for aftershocks.")
else:
    st.info("No data for aftershock analysis.")

st.divider()

# Sortable data table
st.subheader("📋 Event Data")
st.dataframe(
    df_filtered[["datetime", "place", "magnitude", "depth_km", "latitude", "longitude", "tsunami"]]
    .sort_values("datetime", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
    height=400,
)
