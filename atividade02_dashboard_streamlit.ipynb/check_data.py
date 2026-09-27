"""Checks both the Activity 01 reference and the prepared dashboard data.

1. Re-runs the Activity 01 funnel with blank neighborhoods retained and
    compares counts and medians with the delivered notebook.
2. Checks that data/apartamentos_itbi_poa.parquet matches a fresh run of the
    default pipeline, which excludes blank neighborhoods, and respects the
    validity rules.

Usage: python check_data.py   (run prepare_data.py first)
"""

import sys
from pathlib import Path

import pandas as pd

import pipeline

DATA_DIR = Path(__file__).parent / "data"

# Values copied from the outputs of the Activity 01 notebook
REFERENCE_FUNNEL = [326623, 324323, 119493, 119492, 118655, 116282]
REFERENCE_BY_YEAR = {  # ano: (n, median base_de_calculo, median valor_m2)
    2020: (13817, 232000.00, 4326.920),
    2021: (17906, 240000.00, 4283.380),
    2022: (19671, 236000.00, 4491.050),
    2023: (20628, 230000.00, 4522.245),
    2024: (20447, 239690.18, 4715.840),
    2025: (23813, 240000.00, 4756.080),
}
REFERENCE_NEIGHBORHOODS = {  # bairro: (n, median valor_m2)
    "JARDIM EUROPA": (540, 11223.640),
    "TRES FIGUEIRAS": (475, 10403.800),
    "PETROPOLIS": (5847, 6300.560),
    "RESTINGA": (4138, 3252.010),
    "RUBEM BERTA": (2542, 2557.825),
}

failures = []


def check(label, ok):
    print(f"[{'OK' if ok else 'FAIL'}] {label}")
    if not ok:
        failures.append(label)


def main():
    raw = pipeline.load_raw(DATA_DIR / "raw")

    print("== 1. Activity 01 reference (blank neighborhoods retained) ==")
    ref, funnel = pipeline.prepare(raw, drop_blank_bairro=False)
    check(f"funnel {funnel['registros'].tolist()}", funnel["registros"].tolist() == REFERENCE_FUNNEL)

    by_year = ref.groupby("ano").agg(
        n=("valor_m2", "size"),
        value=("base_de_calculo", "median"),
        m2=("valor_m2", "median"),
    )
    for year, (n, value, m2) in REFERENCE_BY_YEAR.items():
        row = by_year.loc[year]
        check(
            f"{year}: n={int(row.n)}, median value={row.value:,.2f}, median R$/m²={row.m2:,.3f}",
            row.n == n and abs(row.value - value) < 0.01 and abs(row.m2 - m2) < 0.001,
        )

    by_neighborhood = ref.groupby("bairro")["valor_m2"].agg(["size", "median"])
    for name, (n, m2) in REFERENCE_NEIGHBORHOODS.items():
        row = by_neighborhood.loc[name]
        check(f"{name}: n={int(row['size'])}, median R$/m²={row['median']:,.3f}",
              row["size"] == n and abs(row["median"] - m2) < 0.001)

    print("\n== 2. Dashboard data (blank neighborhoods excluded) ==")
    df = pd.read_parquet(DATA_DIR / "apartamentos_itbi_poa.parquet")
    expected = pipeline.to_output(pipeline.prepare(raw)[0])
    check(f"parquet has {len(df)} rows, same as a fresh run", len(df) == len(expected))
    check("same values as a fresh run",
          df[expected.columns].reset_index(drop=True).equals(expected.reset_index(drop=True)))
    check("years 2020-2025 only", set(df["ano"]) == set(pipeline.RESOURCE_ID))
    check("value and area > 0", df["base_de_calculo"].gt(0).all() and df["area_constr_privativa"].gt(0).all())
    check("no blank or undefined neighborhood",
          not df["bairro"].isin(["", pipeline.UNDEFINED_ZONE]).any() and df["bairro"].notna().all())
    check("valor_m2 = value / area",
          (df["valor_m2"] - df["base_de_calculo"] / df["area_constr_privativa"]).abs().max() < 0.01)
    check(f"{(~df['tem_poligono']).sum()} records without polygon (expected: JAR ITU SABARA only)",
          set(df.loc[~df["tem_poligono"], "bairro"]) <= {"JAR ITU SABARA"})

    print(f"\n{'All checks passed.' if not failures else f'{len(failures)} check(s) failed.'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
