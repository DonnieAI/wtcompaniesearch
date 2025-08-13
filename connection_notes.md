"""
=====================
POSTGRESQL ACCESS  (Heroku adapted)
"""

# Optional for local dev; Streamlit Cloud ignores .env
try:
    from dotenv import load_dotenv
    if os.getenv("DATABASE_URL") is None:
        load_dotenv()
except Exception:
    pass

def _get_database_url() -> str:
    # Prefer Streamlit secrets; fallback to env for local dev
    url = st.secrets.get("DATABASE_URL") if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets else os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set (in Streamlit secrets or environment).")

    # Normalize driver for SQLAlchemy
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]

    # Ensure SSL on cloud; allow no-SSL locally
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query))
    host = (parsed.hostname or "").lower()
    if host not in {"localhost", "127.0.0.1"}:
        q.setdefault("sslmode", "require")
    url = urlunparse(parsed._replace(query=urlencode(q)))
    return url

def get_engine():
    """Create a SQLAlchemy engine (no Streamlit caching as requested)."""
    return create_engine(_get_database_url(), pool_pre_ping=True, pool_recycle=1800)


def get_engine():
    """Create a SQLAlchemy engine (no Streamlit caching as requested)."""
    return create_engine(_get_database_url(), pool_pre_ping=True, pool_recycle=1800)

@st.cache_data(ttl=15 * 60)
def get_companies_clean() -> pd.DataFrame:
    """
    Load from Postgres and return cleaned companies:
      - COUNTRY_ISO2 not null
      - BUSINESS_DOMAIN not null
      - WEBSITE != 'https://BLANK' (case/space tolerant)
    """
    engine = get_engine()
    sql = 'SELECT * FROM "COMPANIES"."WT_companies_database"'
    df = pd.read_sql(sql, con=engine)

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