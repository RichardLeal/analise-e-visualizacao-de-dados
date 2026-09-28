"""Official neighborhood boundaries (LC 12.112/2016, SMURB/PMPA) and name matching.

ITBI neighborhood names are truncated or abbreviated ("CENTRO HISTORIC",
"STA ROSA LIMA"). They are matched to the official names by normalization,
known abbreviations, explicit overrides and, last, a unique prefix.
"""

import re
import unicodedata
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd

SHAPEFILE_URL = (
    "https://dadosabertos.poa.br/dataset/a7172700-e0e2-4797-bf4a-12f658828568/"
    "resource/1de9991b-ae77-4359-a0cc-daf82fdf1896/download/bairros_lc12112_16.zip"
)

# Prefix abbreviations used by the ITBI base (same as Atividade 01)
ABBREV = {"JAR ": "JARDIM ", "N SRA": "NOSSA SENHORA", "CEL ": "CORONEL "}

# ITBI names that the rules above cannot resolve (normalized ITBI -> normalized official)
OVERRIDES = {
    "CORONEL AP BORGES": "CEL. APARICIO BORGES",
    "CHACARA PEDRAS": "CHACARA DAS PEDRAS",
    "LOMBA PINHEIRO": "LOMBA DO PINHEIRO",
    "MOINHOS VENTO": "MOINHOS DE VENTO",
    "MONT SERRAT": "MONTSERRAT",
    "PARQUE STA FE": "PARQUE SANTA FE",
    "PASSO PEDRAS": "PASSO DAS PEDRAS",
    "SANTA M GORETTI": "SANTA MARIA GORETTI",
    "STA ROSA LIMA": "SANTA ROSA DE LIMA",
    "VL JOAO PESSOA": "VILA JOAO PESSOA",
    "VL SAO JOSE": "VILA SAO JOSE",
}
# Not mapped on purpose: "JAR ITU SABARA" is the former Jardim Itu-Sabará, split
# into Jardim Itu and Jardim Sabará by LC 12.112/2016; no single polygon fits.

SIMPLIFY_TOLERANCE_M = 5  # metres, in the original projected CRS


def norm(name):
    """Strips accents, uppercases and collapses spaces."""
    name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", name).upper().strip()


def expand(name):
    for short, full in ABBREV.items():
        if name.startswith(short):
            name = full + name[len(short):]
    return name


def load_boundaries(cache_dir):
    """Downloads (once) the shapefile and returns one polygon per official name, in WGS84."""
    zip_path = Path(cache_dir) / "bairros_lc12112_16.zip"
    if not zip_path.exists():
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(SHAPEFILE_URL, zip_path)

    gdf = gpd.read_file(f"zip://{zip_path}")
    gdf["NOME"] = gdf["NOME"].str.replace(r"\s+", " ", regex=True).str.strip()
    # Some neighborhoods (e.g. Arquipélago) have several polygons
    gdf = gdf[["NOME", "geometry"]].dissolve(by="NOME", as_index=False)
    gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.rename(columns={"NOME": "bairro_oficial"})
    gdf["key"] = gdf["bairro_oficial"].map(norm)
    return gdf


def build_name_map(itbi_names, official_names):
    """Returns {ITBI name: official name or None}."""
    by_key = {norm(o): o for o in official_names}
    keys = list(by_key)

    def resolve(itbi_name):
        key = norm(itbi_name)
        key = OVERRIDES.get(key, OVERRIDES.get(expand(key), expand(key)))
        if key in by_key:
            return by_key[key]
        candidates = [k for k in keys if k.startswith(key)]
        return by_key[candidates[0]] if len(candidates) == 1 else None

    return {name: resolve(name) for name in itbi_names}
