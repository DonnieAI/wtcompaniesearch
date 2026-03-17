import streamlit as st
import psycopg
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import URL

from utils import apply_style_and_logo

st.set_page_config(page_title="Companies Overview", layout="wide")
apply_style_and_logo()

st.title("Italian Company Search Database")
st.markdown(
    """
    ## Database overview

This database includes **active companies** classified according to the latest available **ATECO code** update.

The **ATECO code** is the standard Italian classification used to identify the **economic activity** of a company.  
Each code corresponds to a specific business sector or activity.

The current selection is based on two dimensions:

- **Provincia (sede legale)**: the province of the company’s registered office
- **Codice ATECO**: the economic activity category associated with the company

By combining these filters, users can explore active companies operating in a specific **territorial area** and within a specific **business sector**.
    """
)

cfg = st.secrets["neon"]

HOST = cfg["host"]
PORT = int(cfg.get("port", 5432))
DBNAME = cfg["dbname"]
USER = cfg["user"]
PASSWORD = cfg["password"]
SSLMODE = cfg.get("sslmode", "require")
CHANNEL_BINDING = cfg.get("channel_binding")


@st.cache_resource
def get_engine():
    query = {"sslmode": SSLMODE}
    if CHANNEL_BINDING:
        query["channel_binding"] = CHANNEL_BINDING

    url = URL.create(
        "postgresql+psycopg",
        username=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        database=DBNAME,
        query=query,
    )

    return create_engine(
        url,
        pool_pre_ping=True,   # important
        pool_recycle=1800     # optional but useful
    )


engine = get_engine()


# optional connection test
try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
    st.success("Database connection OK")
    with st.expander("Connection details"):
        st.write("PostgreSQL version:", version)
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


@st.cache_data
def list_schemas():
    q = text("""
        SELECT schema_name
        FROM information_schema.schemata
        ORDER BY schema_name
    """)
    with engine.connect() as conn:
        return pd.read_sql(q, conn)["schema_name"].tolist()


@st.cache_data
def list_tables(schema_name: str):
    inspector = inspect(engine)
    return inspector.get_table_names(schema=schema_name)


@st.cache_data
def get_unique_sede_legale(schema_name: str, table_name: str):
    q = text(f'''
        SELECT DISTINCT sede_legale
        FROM "{schema_name}"."{table_name}"
        WHERE sede_legale IS NOT NULL
          AND TRIM(sede_legale) <> ''
        ORDER BY sede_legale
    ''')
    with engine.connect() as conn:
        df = pd.read_sql(q, conn)
    return df["sede_legale"].tolist()


def load_table_data(schema_name: str, table_name: str, sede_legale_filter: str | None):
    sql = f'SELECT * FROM "{schema_name}"."{table_name}"'
    params = {}

    if sede_legale_filter and sede_legale_filter != "All":
        sql += ' WHERE sede_legale = :sede_legale'
        params["sede_legale"] = sede_legale_filter

    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


schemas = list_schemas()
default_schema = "COMPANIES"
schema_index = schemas.index(default_schema) if default_schema in schemas else 0

c1, c2, c3 = st.columns([1, 2, 2])

with c1:
    schema_name = st.selectbox("Schema", schemas, index=schema_index)

tables = list_tables(schema_name)
if not tables:
    st.warning(f'No tables found in schema "{schema_name}"')
    st.stop()

default_table = "10.51.20 - Produzione di derivati del latte"
table_index = tables.index(default_table) if default_table in tables else 0

with c2:
    table_name = st.selectbox("Table", tables, index=table_index)

sede_values = get_unique_sede_legale(schema_name, table_name)
sede_options = sede_values if sede_values else ["AVELLINO"]

default_sede = "AVELLINO"
sede_index = sede_options.index(default_sede) if default_sede in sede_options else 0

with c3:
    sede_legale_filter = st.selectbox(
        "Provincia (Sede legale)",
        sede_options,
        index=sede_index
    )

st.markdown("### Results")

cols_to_drop = [
        "denominazione",
        "pec",
        "rea",
        "sede_legale",
        "source_file",
        "stato_impresa",
        "forma_giuridica",
        "codice_fiscale_piva"
    ]




if st.button("Load data", use_container_width=True):
    df = load_table_data(schema_name, table_name, sede_legale_filter)
    df_display = df.drop(columns=cols_to_drop, errors="ignore")
    st.write(f"Rows returned: **{len(df_display)}**")
    st.dataframe(df_display, use_container_width=True, hide_index=True)