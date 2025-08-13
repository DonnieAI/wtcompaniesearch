"""
Pytho code to upload the companies..csv file to the dedicated posgressql
"""

#from pathlib import Path
import pandas as pd
import os
import os
import time


#import psycopg2
from dotenv import load_dotenv

#from urllib.parse import urlparse
#from sqlalchemy import create_engine
import streamlit as st

import requests
from bs4 import BeautifulSoup

import streamlit as st
#from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode



@st.cache_data(ttl=15 * 60)
def get_companies_clean_pd() -> pd.DataFrame:
    """
    Load from Postgres and return cleaned companies:
      - COUNTRY_ISO2 not null
      - BUSINESS_DOMAIN not null
      - WEBSITE != 'https://BLANK' (case/space tolerant)
    """
    df = pd.read_csv("WT_companies_tbl.csv")

    # Trim whitespace in key text columns to reduce false-missing
    for col in ["COUNTRY_ISO2", "BUSINESS_DOMAIN", "WEBSITE"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    mask = (
        df["COUNTRY_ISO2"].notna() &
        (df["COUNTRY_ISO2"] != "") &
        df["BUSINESS_DOMAIN"].notna() &
        (df["BUSINESS_DOMAIN"] != "") &
        (df["WEBSITE"].fillna("").str.strip().str.lower() != "https://blank")
    )

    df_clean = df.loc[mask].reset_index(drop=True)
    return df_clean

def _get_secret(name: str) -> str | None:
    # Prefer Streamlit secrets; fallback to environment variables
    try:
        return st.secrets[name]  # raises KeyError if missing
    except Exception:
        return os.getenv(name)

def google_search(query: str, num_results: int = 4, max_chars: int = 500) -> list[dict]:
    api_key = _get_secret("GOOGLE_API_KEY")
    search_engine_id = _get_secret("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError(
            "Missing GOOGLE_API_KEY or GOOGLE_SEARCH_ENGINE_ID. "
            "Add them to .streamlit/secrets.toml or your environment."
        )

    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": str(num_results),
        "lr": "lang_en"  # only English results
    }

    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        try:
            details = resp.json()
        except Exception:
            details = resp.text
        raise RuntimeError(f"Google CSE request failed [{resp.status_code}]: {details}")

    items = resp.json().get("items", []) or []

    def get_page_content(link: str) -> str:
        try:
            r = requests.get(link, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            out = []
            total = 0
            for w in words:
                lw = len(w) + (1 if total else 0)
                if total + lw > max_chars:
                    break
                out.append(w)
                total += lw
            return " ".join(out)
        except Exception:
            return ""

    enriched = []
    for it in items:
        link = it.get("link", "")
        body = get_page_content(link) if link else ""
        enriched.append({
            "title": it.get("title", ""),
            "link": link,
            "snippet": it.get("snippet", ""),
            "body": body,
        })
        time.sleep(1)  # polite delay

    return enriched

def summarize_web_page(url: str, max_chars: int = 5000) -> str:
    import requests
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching the page: {str(e)}"

    soup = BeautifulSoup(response.content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    content = ""

    for word in words:
        if len(content) + len(word) + 1 > max_chars:
            break
        content += " " + word

    return content.strip() if content else "No readable content found on the page."


def extract_at_words(url: str) -> list[str]:
    import requests
    from bs4 import BeautifulSoup
    import re

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return [f"Error fetching the page: {str(e)}"]

    soup = BeautifulSoup(response.content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    # Find all words that contain "@"
    at_words = re.findall(r"\b\S+@\S+\b", text)
    return list(set(at_words))  # Remove duplicates
