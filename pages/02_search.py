import streamlit as st
from db import get_companies_clean, google_search,summarize_web_page,extract_at_words
import pandas as pd
from pathlib import Path
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
from sqlalchemy import create_engine
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from db import get_companies_clean

st.title("Companies Overview")

# Refresh data button
refresh = st.button("Refresh data")
if refresh:
    st.cache_data.clear()

# Load cleaned data (your cached function)
df_clean = get_companies_clean()

# --- Filters ---
# Build options (include "All")
country_opts = ["All"] + sorted(df_clean["COUNTRY_ISO2"].dropna().unique().tolist())
bdomain_opts = ["All"] + sorted(df_clean["BUSINESS_DOMAIN"].dropna().unique().tolist())
edomain_opts = ["All"] + sorted(df_clean["ENERGY_DOMAIN"].dropna().unique().tolist())

col1, col2, col3 = st.columns(3)
with col1:
    sel_country = st.selectbox("Country", country_opts, index=0)
with col2:
    sel_bdomain = st.selectbox("Business Domain", bdomain_opts, index=0)
with col3:
    sel_edomain = st.selectbox("Energy Domain", edomain_opts, index=0)

# Apply filters
mask = pd.Series(True, index=df_clean.index)
if sel_country != "All":
    mask &= (df_clean["COUNTRY_ISO2"] == sel_country)
if sel_bdomain != "All":
    mask &= (df_clean["BUSINESS_DOMAIN"] == sel_bdomain)
if sel_edomain != "All":
    mask &= (df_clean["ENERGY_DOMAIN"] == sel_edomain)

df_filtered = df_clean.loc[mask].copy()

st.subheader("Filtered Companies")
st.dataframe(
    df_filtered,
    use_container_width=True,
    height=400,
    #Download=False
)


# --- Company website lookup form ---
st.subheader("Find Company Website")

# Company selection dropdown from the filtered dataframe
company_selected = st.selectbox(
    "Select company", 
    sorted(df_filtered["COMPANY"].unique())
)

# Show the website directly when a company is chosen
if company_selected:
    website = df_filtered.loc[df_filtered["COMPANY"] == company_selected, "WEBSITE"].iloc[0]
    st.success(f"Website: {website}")
    st.session_state["selected_website"] = website
    

st.subheader("Google Search")

query = st.text_input("Search query", value=st.session_state.get("selected_website", ""))

if st.button("Fetch & Summarize"):
    if query.strip():
        with st.spinner("Fetching..."):
            result_text = summarize_web_page(query)  # returns long text

        # --- Summary preview ---
        preview = result_text.strip()[:300]
        st.markdown("**Summary (preview):**")
        st.markdown(preview)

        # --- Extract emails ---
        emails = extract_at_words(query)  # <-- call the function
        if emails:
            st.markdown("**Emails found:**")
            for e in emails:
                st.code(e)
        else:
            st.info("No emails found in the content.")

        # --- Full content ---
        with st.expander("Show full content"):
            for para in [p for p in result_text.split("\n") if p.strip()]:
                st.markdown(para)
    else:
        st.warning("Please enter a URL or search query.")

if st.button("Run Google Search"):
    if query.strip():
        with st.spinner("Fetching..."):
            results = google_search(query)
        for r in results:
            st.write(f"[{r['title']}]({r['link']})")
            st.caption(r['snippet'])
    else:
        st.warning("Please enter a search query.")