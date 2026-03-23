import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import random
st.title("Live API + Heavy DataFrame Processing")

if "raw_rows" not in st.session_state:
    st.session_state.raw_rows = []

def fetch_data():
    product_id = random.randint(1, 100)
    url = f"https://dummyjson.com/products/{product_id}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "price": data["price"],
        "title": data["title"]
    }

    
@st.cache_data
def transform_data(rows_tuple):
    # convert immutable input back to dataframe
    df = pd.DataFrame(rows_tuple, columns=["time", "price"])

    # heavy processing examples
    df["rolling_mean_5"] = df["price"].rolling(5).mean()
    df["pct_change"] = df["price"].pct_change() * 100
    df["price_diff"] = df["price"].diff()

    return df

@st.fragment(run_every="10s")
def live_feed():
    try:
        new_row = fetch_data()
        st.session_state.raw_rows.append((new_row["time"], new_row["price"]))

        # keep last 100 rows only
        st.session_state.raw_rows = st.session_state.raw_rows[-100:]

        df = transform_data(tuple(st.session_state.raw_rows))

        st.metric("Current BTC Price", f"${df.iloc[-1]['price']:,.2f}")
        st.dataframe(df, use_container_width=True)
        st.line_chart(df.set_index("time")[["price", "rolling_mean_5"]])

    except Exception as e:
        st.error(f"Error: {e}")

live_feed()
