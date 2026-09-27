"""Dashboard: apartment values in Porto Alegre from ITBI records (2020-2025).

Run: streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_apartments():
    return pd.read_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet")


st.set_page_config(page_title="Apartamentos em Porto Alegre — ITBI", layout="wide")
st.title("Quanto custa um apartamento em Porto Alegre?")

df = load_apartments()
st.caption(f"{len(df):,} apartamentos com ITBI entre 2020 e 2025".replace(",", "."))

median_value_by_year = (
    df.groupby("ano", as_index=False)["base_de_calculo"]
    .median()
    .sort_values("ano")
)

fig = px.line(
    median_value_by_year,
    x="ano",
    y="base_de_calculo",
    markers=True,
    title="Valor mediano dos apartamentos por ano",
    labels={
        "ano": "Ano",
        "base_de_calculo": "Base de cálculo mediana (R$)",
    },
)
fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f", showgrid=True)
fig.update_traces(
    hovertemplate="Ano: %{x}<br>Base de cálculo mediana: R$ %{y:,.0f}<extra></extra>"
)
st.plotly_chart(fig, width="stretch")

# TODO (T06-T12): filters, KPIs and remaining charts — see docs/escopo.md
