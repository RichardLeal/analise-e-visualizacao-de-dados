"""Streamlit host for the viewport-sized territorial dashboard."""
import base64
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dashboard_view import build_payload, default_state

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

@st.cache_data
def load_apartments():
    return pd.read_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet")

@st.cache_data
def load_boundaries():
    return json.loads((DATA_DIR / "bairros_poa.geojson").read_text(encoding="utf-8"))

st.set_page_config(page_title="Mapa Imobiliário POA", page_icon="🗺️", layout="wide",
                   initial_sidebar_state="collapsed")
# Remove Streamlit's document padding, not overflow. The component owns its viewport grid.
st.html("""
<style>
[data-testid="stHeader"], [data-testid="stToolbar"] {display:none;}
[data-testid="stMainBlockContainer"] {padding:0!important;max-width:none!important;}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {gap:0!important;}
[data-testid="stElementContainer"]:has(iframe) {line-height:0;}
iframe[title="dashboard.desktop_dashboard"] {display:block;border:0;}
</style>
""")
df = load_apartments()
boundaries = load_boundaries()
state = st.session_state.get("dashboard_state", default_state(df))
payload = build_payload(df, boundaries, state)
crest = "data:image/svg+xml;base64," + base64.b64encode(
    (ROOT / "assets/brasao_porto_alegre.svg").read_bytes()).decode()
desktop_dashboard = components.declare_component("desktop_dashboard", path=str(ROOT / "dashboard"))
event = desktop_dashboard(payload=payload, crest=crest, default=None, key="desktop_dashboard")
if event and event.get("nonce") != st.session_state.get("dashboard_nonce"):
    st.session_state.dashboard_nonce = event["nonce"]
    st.session_state.dashboard_state = event["state"]
    st.rerun()
