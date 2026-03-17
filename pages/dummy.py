import streamlit as st
import psycopg
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------- 1) Read secrets ----------
cfg = st.secrets["neon"]

HOST = cfg["host"]
PORT = int(cfg.get("port", 5432))
DBNAME = cfg["dbname"]
USER = cfg["user"]
PASSWORD = cfg["password"]
SSLMODE = cfg.get("sslmode", "require")
CHANNEL_BINDING = cfg.get("channel_binding")  # optional

st.title("Neon PostgreSQL (Streamlit secrets) test")

# ---------- 2) psycopg (v3) connection test ----------
try:
    conn_kwargs = dict(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        sslmode=SSLMODE,
    )
    if CHANNEL_BINDING:
        conn_kwargs["channel_binding"] = CHANNEL_BINDING

    with psycopg.connect(**conn_kwargs) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]

    st.success("Database connection OK")
    st.write("PostgreSQL version:", version)

except Exception as e:
    st.error(f"psycopg connection failed: {e}")
    st.stop()

# ---------- 3) SQLAlchemy engine (psycopg v3) ----------
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

try:
    engine = create_engine(url)
    with engine.connect() as c:
        c.execute(text("SELECT 1"))
    st.success("SQLAlchemy engine OK")
except Exception as e:
    st.error(f"SQLAlchemy engine failed: {e}")
    st.stop()

# ---------- 4) Read a table ----------
schema_name = st.text_input("Schema", value="COMPANIES")
table_name = st.text_input("Table", value="ateco_telemaco_it")

if st.button("Load table"):
    try:
        df = pd.read_sql_table(table_name=table_name, con=engine, schema=schema_name)
        st.write(f"Rows: {len(df)}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Reading table failed: {e}")