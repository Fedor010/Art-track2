import time
import io
import requests
import pandas as pd
import streamlit as st
from pytrends.request import TrendReq

# Your Yandex OAuth Token
YANDEX_OAUTH_TOKEN = "your_yandex_token_here"
YANDEX_API_URL = "https://api.direct.yandex.com/json/v5/forecasts"

# Region code mappings for Google and Yandex
REGIONS = {
    "Russia": "RU",
    "Ukraine": "UA",
    "Kazakhstan": "KZ",
    "Belarus": "BY",
    "United States": "US",
    "Germany": "DE",
    "France": "FR",
}

# Yandex Wordstat GeoIDs for regions (must be a list of ints)
YANDEX_GEO_IDS = {
    "RU": [225],
    "UA": [143],
    "KZ": [193],
    "BY": [149],
    "US": [187],
    "DE": [77],
    "FR": [83],
}

# Languages for Google Trends & Yandex Suggest
LANGUAGES = {
    "Russian": "ru",
    "English": "en",
    "Ukrainian": "uk",
    "Kazakh": "kk",
}

def geo_to_yandex_geo(google_geo_code):
    return YANDEX_GEO_IDS.get(google_geo_code, [])

def get_yandex_search_count(keyword, region_code):
    headers = {
        "Authorization": f"Bearer {YANDEX_OAUTH_TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    geo_ids = geo_to_yandex_geo(region_code)
    payload = {
        "method": "Get",
        "params": {
            "SelectionCriteria": {
                "GeoID": geo_ids,
                "Keywords": [keyword]
            }
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

def get_google_trends_related(keyword, geo='RU', timeframe='today 12-m', lang='ru'):
    pytrends = TrendReq(hl=lang, tz=180)
    results = []
    try:
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries().get(keyword)
        top = related.get('top') if related else None
        if top is not None:
            for _, row in top.iterrows():
                count = get_yandex_search_count(row["query"], region_code=geo)
                results.append((row["query"], count))
    except Exception as e:
        st.warning(f"Google Trends error for '{keyword}': {e}")
    return results

def get_yandex_suggest(keyword, lang="ru"):
    url = "https://suggest.yandex.net/suggest-ya.cgi"
    params = {
        "part": keyword,
        "lang": lang,
        "uil": lang,
        "v": "4",
        "search_type": "suggest"
    }
    headers = {
        "User-Agent": "keyword-agent/1.0"
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        suggestions = r.json()[1]
        return suggestions
    except Exception as e:
        st.error(f"Yandex Suggest error for '{keyword}': {e}")
        return []

# Streamlit UI
st.title("Keyword Research App")

keyword = st.text_input("Enter seed keyword (in Russian)")

region_name = st.selectbox("Select region", list(REGIONS.keys()), index=0)
lang_name = st.selectbox("Select language", list(LANGUAGES.keys()), index=0)

months = st.selectbox("Select timeframe (months back)", list(range(1, 13)), index=5)
run_btn = st.button("Run and Download")

if run_btn:
    if not keyword.strip():
        st.error("Please enter a keyword.")
    else:
        geo_code = REGIONS[region_name]
        lang_code = LANGUAGES[lang_name]
        timeframe = f"today {months}-m"

        with st.spinner("Fetching Google Trends related keywords and Yandex search counts..."):
            trends_data = get_google_trends_related(keyword, geo=geo_code, timeframe=timeframe, lang=lang_code)

        with st.spinner("Fetching Yandex Suggest keywords..."):
            yandex_suggest_data = get_yandex_suggest(keyword, lang=lang_code)

        if not trends_data:
            st.info("No Google Trends related keywords found.")
        else:
            df_trends = pd.DataFrame(trends_data, columns=["Keyword", "Monthly Searches (Yandex)"])
            st.subheader(f"Google Trends Related Keywords + Yandex Monthly Search Counts ({region_name}, {lang_name})")
            st.dataframe(df_trends)

            buffer_trends = io.BytesIO()
            with pd.ExcelWriter(buffer_trends, engine='openpyxl') as writer:
                df_trends.to_excel(writer, index=False)
            buffer_trends.seek(0)

            st.download_button(
                label="Download Google Trends Data as Excel",
                data=buffer_trends,
                file_name="google_trends_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if not yandex_suggest_data:
            st.info("No Yandex Suggest keywords found.")
        else:
            df_yandex_suggest = pd.DataFrame(yandex_suggest_data, columns=["Keyword"])
            st.subheader(f"Yandex Suggest Keywords (no volume data) ({region_name}, {lang_name})")
            st.dataframe(df_yandex_suggest)

            buffer_suggest = io.BytesIO()
            with pd.ExcelWriter(buffer_suggest, engine='openpyxl') as writer:
                df_yandex_suggest.to_excel(writer, index=False)
            buffer_suggest.seek(0)

            st.download_button(
                label="Download Yandex Suggest Data as Excel",
                data=buffer_suggest,
                file_name="yandex_suggest_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
