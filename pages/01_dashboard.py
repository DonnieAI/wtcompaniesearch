# pages/01_dashbord

#import os
import streamlit as st
import pandas as pd
from pathlib import Path
import pandas as pd

#import psycopg2
from dotenv import load_dotenv

#from urllib.parse import urlparse
#from sqlalchemy import create_engine

import plotly.express as px

import plotly.graph_objects as go

from db import get_companies_clean_pd

#-----------------------------------------------------------------------
st.set_page_config(page_title="map", layout="wide")
from utils import apply_style_and_logo
apply_style_and_logo()


st.title("Companies Overview")

refresh = st.button("Refresh data")
if refresh:
    st.cache_data.clear()

df_clean=get_companies_clean_pd()

st.markdown(f"**Wavetransition companies database** based on **{df_clean.shape[0]}** records")



def prepare_sunburst_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare data for the sunburst chart.
    """
    df_clean = df.copy()

    # Fill missing values
    df_clean['COUNTRY_ISO2'] = df_clean['COUNTRY_ISO2'].fillna('Unknown')
    df_clean['LISTED'] = df_clean['LISTED'].fillna('No')
    df_clean['LISTED'] = df_clean['LISTED'].apply(lambda x: 'Yes' if str(x).strip().lower() == 'yes' else 'No')

    df_clean['BUSINESS_DOMAIN'] = df_clean['BUSINESS_DOMAIN'].fillna('Unknown')
    df_clean['ENERGY_DOMAIN'] = df_clean['ENERGY_DOMAIN'].fillna('Other')

    # Create a new column: SUBDOMAIN
    df_clean['SUBDOMAIN'] = df_clean.apply(
        lambda row: row['ENERGY_DOMAIN'] if row['BUSINESS_DOMAIN'].strip().upper() == 'ENERGY' else 'Other',
        axis=1
    )

    return df_clean

df_clean=prepare_sunburst_data(df_clean)

def build_sunburst_go_with_custom_colors(df: pd.DataFrame) -> go.Figure:
    # Filter the data
    df_filtered = df[
        df['COUNTRY_ISO2'].notna() &
        df['BUSINESS_DOMAIN'].notna() &
        df['ENERGY_DOMAIN'].notna() &
        (df['WEBSITE'].str.strip().str.lower() != 'https://blank')
    ].copy()

    # Define subdomain only for ENERGY
    df_filtered['SUBDOMAIN'] = df_filtered.apply(
        lambda row: row['ENERGY_DOMAIN'] if row['BUSINESS_DOMAIN'].upper().strip() == 'ENERGY' else 'Other',
        axis=1
    )

    # Prepare counts
    country_counts = df_filtered['COUNTRY_ISO2'].value_counts()
    country_business = df_filtered.groupby(['COUNTRY_ISO2', 'BUSINESS_DOMAIN']).size()
    business_subdomain = df_filtered.groupby(['COUNTRY_ISO2', 'BUSINESS_DOMAIN', 'SUBDOMAIN']).size()

    labels = []
    parents = []
    values = []
    hover_texts = []
    colors = []

    # Define fixed business domain colors
    business_domain_colors = {
        'ENERGY': '#636EFA',
        'CERAMICS': '#EF553B',
        #'TRANSPORT': '#00CC96',
        'Unknown': '#B6E880',
        #'Other': '#AAAAAA'
    }

    # Step 1: Countries — assign unique colors
    country_color_palette = px.colors.qualitative.Bold
    country_list = country_counts.index.tolist()
    country_color_map = {
        country: country_color_palette[i % len(country_color_palette)]
        for i, country in enumerate(country_list)
    }

    for country in country_list:
        count = country_counts[country]
        labels.append(country)
        parents.append("")
        values.append(count)
        hover_texts.append(f"Country: {country}<br>Companies: {count}")
        colors.append(country_color_map[country])

    # Step 2: Business domains
    for (country, domain), count in country_business.items():
        label = f"{domain} ({country})"
        parent = country
        labels.append(label)
        parents.append(parent)
        values.append(count)
        hover_texts.append(f"Country: {country}<br>Business Domain: {domain}<br>Companies: {count}")
        colors.append(business_domain_colors.get(domain.upper().strip(), '#999999'))

    # Step 3: Subdomains
    for (country, domain, sub), count in business_subdomain.items():
        label = f"{sub} ({count})"  # Show only subdomain and count
        parent = f"{domain} ({country})"
        labels.append(label)
        parents.append(parent)
        values.append(count)
        hover_texts.append(
            f"Subdomain: {sub}<br>Companies: {count}"
        )
        colors.append(business_domain_colors.get(domain.upper().strip(), '#999999'))

    # Create the sunburst
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        hovertext=hover_texts,
        hoverinfo="text",
        marker=dict(colors=colors),
        branchvalues="total"
    ))

    fig.update_layout(
        title="Company Hierarchy - fullscrean to be activated",
        margin=dict(t=40, l=0, r=0, b=0)
    )

    return fig

#df = df_out # replace this with your actual variable

df_prepared = prepare_sunburst_data(df_clean)
fig=build_sunburst_go_with_custom_colors(df_prepared)


#st.write(df_clean.shape)
st.plotly_chart(fig, use_container_width=False,height=8000)
#st.dataframe(df_clean.head())