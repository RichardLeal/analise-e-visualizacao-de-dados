"""Data preparation pipeline for the ITBI apartments dataset (Porto Alegre, 2020-2025).

Reproduces the funnel from Atividade 01 (section 3.2.9) so the dashboard and the
notebook use exactly the same rules. Each step records how many rows remain.
"""

import time
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://dadosabertos.poa.br/api/3/action/datastore_search"

RESOURCE_ID = {
    2020: "60256fcf-9ae6-4adf-b0b4-b6b45fb4b34b",
    2021: "150848b4-0d01-4ffb-96e0-f5f2a276f5ef",
    2022: "102520c0-3edc-4f85-947f-6a98b96ed160",
    2023: "2a4b0aee-7126-4323-936d-5f82fd04aeef",
    2024: "4947bed6-6be6-40e6-a120-42957e745da5",
    2025: "e46f56f3-ac8a-4513-b155-5d3038a275b2",
}

REQUEST_LIMIT = 10000        # records per API request
MAX_RETRIES = 5              # attempts per batch before giving up
RETRY_BACKOFF = 3            # seconds; grows linearly per attempt
REQUEST_TIMEOUT = (10, 120)  # (connect, read) in seconds

UNDEFINED_ZONE = "ZN INDEFINIDA 2"
OUTLIER_QUANTILES = (0.01, 0.99)

# Columns kept in the dataset consumed by the dashboard
OUTPUT_COLUMNS = [
    "ano",
    "data_estimativa",
    "bairro",
    "base_de_calculo",
    "area_constr_privativa",
    "valor_m2",
    "ano_construcao",
    "perc_transmitido",
    "situacao",
]


# --- API access ---------------------------------------------------------------

def fetch_itbi_batch(resource_id, offset):
    params = {"resource_id": resource_id, "limit": REQUEST_LIMIT, "offset": offset}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()["result"]
        except requests.exceptions.RequestException as error:
            if attempt == MAX_RETRIES:
                raise
            wait = RETRY_BACKOFF * attempt
            print(f"[WARN] offset={offset} attempt={attempt}/{MAX_RETRIES} wait={wait}s error={error}")
            time.sleep(wait)


def load_itbi_year(year):
    """Loads every record of one year from the API, in batches."""
    resource_id = RESOURCE_ID[year]
    first = fetch_itbi_batch(resource_id, 0)
    records = first["records"]

    for offset in range(REQUEST_LIMIT, first["total"], REQUEST_LIMIT):
        records.extend(fetch_itbi_batch(resource_id, offset)["records"])

    df = pd.DataFrame(records)
    df["year"] = year
    print(f"[INFO] {year}: {len(df)} records")
    return df


def load_raw(cache_dir=None, refresh=False):
    """Loads all years, using a local pickle cache so the API is hit only once.

    Pickle keeps the exact values returned by the API (mixed types included),
    so re-running from cache gives the same result as a fresh download.
    """
    frames = []
    for year in RESOURCE_ID:
        cache_file = Path(cache_dir) / f"itbi_{year}.pkl" if cache_dir else None
        if cache_file and cache_file.exists() and not refresh:
            df = pd.read_pickle(cache_file)
        else:
            df = load_itbi_year(year)
            if cache_file:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_pickle(cache_file)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# --- Funnel -------------------------------------------------------------------

def prepare(df_raw, drop_blank_bairro=True):
    """Applies the Atividade 01 funnel and returns (df, funnel).

    drop_blank_bairro=False reproduces Atividade 01 exactly; True also drops
    records with an empty `bairro`, which slipped through in Atividade 01.
    """
    funnel = []

    def step(name, frame):
        funnel.append({"etapa": name, "registros": len(frame)})

    df = df_raw.copy()
    step("Registros consolidados (2020-2025)", df)

    # Types
    df["data_estimativa"] = pd.to_datetime(df["data_estimativa"], errors="coerce")
    df["base_de_calculo"] = pd.to_numeric(df["base_de_calculo"], errors="coerce")
    df["area_constr_privativa"] = pd.to_numeric(df["area_constr_privativa"], errors="coerce")
    df["_id"] = pd.to_numeric(df["_id"], errors="raise")

    # Original order matters: extra units of a guide follow its first unit
    df = df.sort_values(["year", "_id"]).reset_index(drop=True)

    # Full duplicates (the API _id is only a technical key)
    duplicate_columns = [c for c in df.columns if c != "_id"]
    df = df.loc[~df.duplicated(subset=duplicate_columns, keep="first")].reset_index(drop=True)
    step("Sem duplicatas", df)

    # Guide reconstruction: a new guide starts at each row with base_de_calculo
    new_year = df["year"].ne(df["year"].shift())
    new_guide = df["base_de_calculo"].notna()
    df["guide_group_id"] = (new_year | new_guide).cumsum()
    df["guide_unit_count"] = df.groupby("guide_group_id")["guide_group_id"].transform("size")
    df["is_multi_unit"] = df["guide_unit_count"] > 1

    # Apartments in single-unit guides
    df = df.loc[df["finalidade_construcao"].eq("APARTAMENTO") & ~df["is_multi_unit"]].copy()
    step("Apartamentos em guias de unidade única", df)

    # Valid value and private area
    df = df.loc[
        df["base_de_calculo"].notna() & df["base_de_calculo"].gt(0)
        & df["area_constr_privativa"].notna() & df["area_constr_privativa"].gt(0)
    ].copy()
    step("Valor e área privativa válidos", df)

    # Light type fixes for the analysis
    df = df.rename(columns={"year": "ano"})
    df["ano_construcao"] = pd.to_numeric(df["ano_construcao"], errors="coerce").astype("Int64")
    df["perc_transmitido"] = pd.to_numeric(df["perc_transmitido"], errors="coerce")
    df["bairro"] = df["bairro"].astype("string").str.strip().str.upper()

    # Geographic cut
    df = df.loc[df["bairro"].ne(UNDEFINED_ZONE)].copy()
    step(f"Sem {UNDEFINED_ZONE}", df)

    if drop_blank_bairro:
        df = df.loc[df["bairro"].fillna("").ne("")].copy()
        step("Sem bairro vazio", df)

    # Value per m2
    df["valor_m2"] = (df["base_de_calculo"] / df["area_constr_privativa"]).round(2)

    # Outliers: keep P1-P99 of valor_m2
    low, high = df["valor_m2"].quantile(list(OUTLIER_QUANTILES))
    df = df.loc[df["valor_m2"].between(low, high)].copy()
    step(f"Sem atípicos (valor/m² entre R$ {low:,.2f} e R$ {high:,.2f})", df)

    return df.reset_index(drop=True), pd.DataFrame(funnel)


def to_output(df):
    """Keeps only the columns used by the dashboard."""
    return df[OUTPUT_COLUMNS].reset_index(drop=True)
