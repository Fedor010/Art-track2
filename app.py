import time
import io
import requests
import pandas as pd
import streamlit as st
from pytrends.request import TrendReq

# Your Yandex OAuth Token (replace with your actual token)
YANDEX_OAUTH_TOKEN = "y0__xC_vqmrCBjoxDkgs_n3iBRWlmEw7FrBy23_f06ynwGWfHUFPA"
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

# Languages for Google Trends & Yandex Suggest
LANGUAGES = {
    "Russian": "ru",
    "English": "en",
    "Ukrainian": "uk",
    "Kazakh": "kk",
}

def get_google_trends_related(keyword, geo='RU', timeframe='today 12-m', lang='ru'):
    pytrends = TrendReq(hl=lang, tz=180)
    results = []
    try:
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries().get(keyword)
        top = related.get('top') if related else None
        if top is not None:
            for _, row in top.iterrows():
                results.append(row["query"])
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

months = st.selectbox("Select timeframe (months back)", list(range(1, 13)), index=11)  # default 12 months

if st.button("Run and Download"):
    if not keyword.strip():
        st.error("Please enter a keyword.")
    else:
        geo_code = REGIONS[region_name]
        lang_code = LANGUAGES[lang_name]
        timeframe = f"today {months}-m"

        with st.spinner("Fetching Google Trends related keywords..."):
            google_data = get_google_trends_related(keyword, geo=geo_code, timeframe=timeframe, lang=lang_code)

        with st.spinner("Fetching Yandex Suggest keywords..."):
            yandex_suggest_data = get_yandex_suggest(keyword, lang=lang_code)

        # Google Trends Keywords Table (no volume)
        if google_data:
            df_google = pd.DataFrame(google_data, columns=["Keyword"])
            st.subheader("Google Trends Related Keywords")
            st.dataframe(df_google)
            buffer_google = io.BytesIO()
            with pd.ExcelWriter(buffer_google, engine='openpyxl') as writer:
                df_google.to_excel(writer, index=False)
            buffer_google.seek(0)
            st.download_button(
                "Download Google Trends Data as Excel",
                buffer_google,
                file_name="google_trends_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No Google Trends related keywords found.")

        # Yandex Suggest Keywords Table (no volume)
        if yandex_suggest_data:
            df_yandex = pd.DataFrame(yandex_suggest_data, columns=["Keyword"])
            st.subheader("Yandex Suggest Keywords")
            st.dataframe(df_yandex)
            buffer_yandex = io.BytesIO()
            with pd.ExcelWriter(buffer_yandex, engine='openpyxl') as writer:
                df_yandex.to_excel(writer, index=False)
            buffer_yandex.seek(0)
            st.download_button(
                "Download Yandex Suggest Data as Excel",
                buffer_yandex,
                file_name="yandex_suggest_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No Yandex Suggest keywords found.")
