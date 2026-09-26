"""Dashboard: apartment values in Porto Alegre from ITBI records (2020-2025).

Run: streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_apartments():
    return pd.read_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet")


st.set_page_config(page_title="Apartamentos em Porto Alegre — ITBI", layout="wide")
st.title("Quanto custa um apartamento em Porto Alegre?")

df = load_apartments()
st.caption(f"{len(df):,} apartamentos com ITBI entre 2020 e 2025".replace(",", "."))

# TODO (T06-T12): filters, KPIs and charts — see docs/escopo.md
