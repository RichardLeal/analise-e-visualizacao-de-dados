"""Dashboard: apartment values in Porto Alegre from ITBI records (2020-2025).

Run: streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from charts import (
    build_neighborhood_record_count_map,
    build_neighborhood_value_map,
    build_yearly_median_chart,
)

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_apartments():
    return pd.read_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet")


@st.cache_data
def load_boundaries():
    return json.loads((DATA_DIR / "bairros_poa.geojson").read_text(encoding="utf-8"))


st.set_page_config(page_title="Apartamentos em Porto Alegre — ITBI", layout="wide")
title_column, crest_column = st.columns([0.86, 0.14], vertical_alignment="center")
with title_column:
    st.title(":blue[Quanto custa um apartamento em Porto Alegre?]")
with crest_column:
    with st.container(horizontal_alignment="right"):
        st.image(Path(__file__).parent / "assets" / "brasao_porto_alegre.svg", width=86)

df = load_apartments()
min_year = int(df["ano"].min())
max_year = int(df["ano"].max())
year_range = st.sidebar.slider(
    "Período (ano)",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
    key="year_range",
)
df_filtered = df.loc[df["ano"].between(*year_range)]

st.caption(
    f"{len(df_filtered):,} apartamentos com ITBI entre {year_range[0]} e {year_range[1]}"
    .replace(",", ".")
)

st.plotly_chart(build_yearly_median_chart(df_filtered), width="stretch")

st.subheader(":blue[Valor mediano por m² por bairro]")
st.caption(
    "A cor representa a mediana do valor por m² das transações em cada bairro. "
    "Bairros sem transações aparecem em cinza."
)
boundaries = load_boundaries()
st_folium(
    build_neighborhood_value_map(df_filtered, boundaries),
    width=None,
    height=650,
    key="neighborhood_value_map_city_only",
)

st.subheader(":blue[Total de registros por bairro]")
st.caption(
    "A cor representa a quantidade de registros no período selecionado. "
    "Bairros sem registros aparecem em branco; o território fora de Porto Alegre aparece esmaecido."
)
st_folium(
    build_neighborhood_record_count_map(df_filtered, boundaries),
    width=None,
    height=650,
    key="neighborhood_record_count_map",
)

boundary_names = {
    feature["properties"]["bairro_oficial"] for feature in boundaries["features"]
}
unmapped = df_filtered.loc[~df_filtered["bairro_oficial"].isin(boundary_names)]
if not unmapped.empty:
    unmapped_counts = unmapped["bairro"].value_counts()
    unmapped_summary = ", ".join(
        f"{neighborhood} ({count} registros)"
        for neighborhood, count in unmapped_counts.items()
    )
    st.caption(f"Sem polígono oficial, portanto fora do mapa: {unmapped_summary}.")

# TODO (T06-T12): filters, KPIs and remaining charts — see docs/escopo.md
