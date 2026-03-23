import streamlit as st
from load_function import load_data
st.title("Geo Mapping")
st.slider("select a number", 0, 100, 50)

data_load_state=st.text("Loading data...")
with st.form("my_form"):
    data=load_data(10)
    count_data=len(data)
    st.metric(label="Number of rows", value=count_data, delta="10")

    edited = st.data_editor(data, num_rows="dynamic")

    st.map(data)
data_load_state.text("Loading data...done!")
import time
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

st.title("Live Bitcoin Price (CoinGecko API)")

# Session state to store history
if "rows" not in st.session_state:
    st.session_state.rows = []

def fetch_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    return data["bitcoin"]["usd"]

@st.fragment(run_every="5s")
def live_feed():
    try:
        price = fetch_btc_price()
        now = datetime.now().strftime("%H:%M:%S")

        st.session_state.rows.append({
            "time": now,
            "price_usd": price
        })

        # keep only latest 50 points
        st.session_state.rows = st.session_state.rows[-50:]

        df = pd.DataFrame(st.session_state.rows)

        st.metric("Current BTC Price", f"${price:,.2f}")
        st.dataframe(df, use_container_width=True)
        st.line_chart(df.set_index("time")["price_usd"])

    except requests.exceptions.RequestException as e:
        st.error(f"API error: {e}")

live_feed()
st.page_link("app.py", label="Home", icon="🏠")
st.page_link("pages/page1.py", label="Page 1", icon="1️⃣")
st.page_link("pages/page2.py", label="Page 2", icon="2️⃣", disabled=True)
st.page_link("https://www.google.com", label="Home", icon="🔗")
