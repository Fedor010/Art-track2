import time
import requests
import pandas as pd
import streamlit as st
from pytrends.request import TrendReq

# Constants and Yandex API setup
YANDEX_OAUTH_TOKEN = "y0__xC_vqmrCBjoxDkgs_n3iBRWlmEw7FrBy23_f06ynwGWfHUFPA"  # Replace with your token
YANDEX_API_URL = "https://api.direct.yandex.com/json/v5/forecasts"

pytrends = TrendReq(hl='ru-RU', tz=180)

def get_yandex_search_count(keyword):
    headers = {
        "Authorization": f"Bearer {YANDEX_OAUTH_TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "method": "Get",
        "params": {
            "SelectionCriteria": {"Keywords": [keyword]}
        }
    }
    try:
        r = requests.post(YANDEX_API_URL, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("result", {}).get("Forecast", {}).get("Impressions", None)
    except Exception as e:
        st.error(f"Yandex Wordstat error for '{keyword}': {e}")
        return None

def get_google_trends_related(keyword, geo='RU', timeframe='today 12-m'):
    results = []
    try:
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries().get(keyword)
        top = related.get('top') if related else None
        if top is not None:
            for _, row in top.iterrows():
                count = get_yandex_search_count(row["query"])
                results.append((row["query"], count))
    except Exception as e:
        st.warning(f"Google Trends error for '{keyword}': {e}")
    return results

# Streamlit UI
st.title("Keyword Research App")

keyword = st.text_input("Enter seed keyword (in Russian)")
months = st.selectbox("Select timeframe (months back)", list(range(1, 13)), index=5)
run_btn = st.button("Run and Download")

if run_btn:
    if not keyword.strip():
        st.error("Please enter a keyword.")
    else:
        timeframe = f"today {months}-m"
        with st.spinner("Fetching related searches..."):
            data = get_google_trends_related(keyword, timeframe=timeframe)
        if not data:
            st.info("No related keywords found.")
        else:
            df = pd.DataFrame(data, columns=["Keyword", "Monthly Searches (Yandex)"])
            st.dataframe(df)
            towrite = df.to_excel(index=False)
            st.download_button(
                label="Download as Excel",
                data=towrite,
                file_name="keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
