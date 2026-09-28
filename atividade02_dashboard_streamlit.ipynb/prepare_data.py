"""Builds the files used by the dashboard.

Usage:
    python prepare_data.py            # uses the local API cache in data/raw when present
    python prepare_data.py --refresh  # downloads everything again

Outputs (in data/):
    apartamentos_itbi_poa.parquet  analytical dataset (one row per apartment)
    bairros_poa.geojson            official neighborhood boundaries (WGS84)
    bairros_correspondencia.csv    ITBI name -> official name
    funil.csv                      rows remaining after each preparation step
"""

import argparse
from pathlib import Path

import geo
import pipeline

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="ignore the local cache and download again")
    args = parser.parse_args()

    print("[1/4] Loading ITBI 2020-2025 from the Porto Alegre open data API...")
    raw = pipeline.load_raw(RAW_DIR, refresh=args.refresh)

    print("[2/4] Applying the preparation funnel...")
    df, funnel = pipeline.prepare(raw)
    print(funnel.to_string(index=False))

    print("[3/4] Matching neighborhoods to the official boundaries...")
    boundaries = geo.load_boundaries(RAW_DIR)
    name_map = geo.build_name_map(sorted(df["bairro"].unique()), boundaries["bairro_oficial"])

    out = pipeline.to_output(df)
    official = out["bairro"].map(name_map)
    out["tem_poligono"] = official.notna()
    # Without a polygon, keep the ITBI name so the record still counts in the charts
    out["bairro_oficial"] = official.fillna(out["bairro"]).astype("string")

    unmatched = sorted(k for k, v in name_map.items() if v is None)
    print(f"Unmatched ITBI names: {unmatched} ({(~out['tem_poligono']).sum()} records)")

    print("[4/4] Writing files...")
    DATA_DIR.mkdir(exist_ok=True)
    out.to_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet", index=False)
    boundaries[["bairro_oficial", "geometry"]].to_file(DATA_DIR / "bairros_poa.geojson", driver="GeoJSON")
    (
        out.groupby(["bairro", "bairro_oficial", "tem_poligono"]).size()
        .rename("registros").reset_index()
        .to_csv(DATA_DIR / "bairros_correspondencia.csv", index=False)
    )
    funnel.to_csv(DATA_DIR / "funil.csv", index=False)
    print(f"Done: {len(out)} apartments in {DATA_DIR}")


if __name__ == "__main__":
    main()
