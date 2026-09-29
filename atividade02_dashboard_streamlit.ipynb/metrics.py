"""Pure calculations for context, profile and neighborhood comparisons."""
import pandas as pd

DEFAULT_MIN_NEIGHBORHOOD_RECORDS = 100
METRICS = {
    "valor_m2": "Valor por m² mediano (R$/m²)",
    "base_de_calculo": "Base de cálculo mediana (R$)",
    "registros": "Número de registros",
    "compatibilidade": "Compatibilidade histórica (%)",
    "variacao": "Variação observada do valor/m² (%)",
}

def format_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_currency_br(value):
    return "—" if pd.isna(value) else "R$ " + format_number(value)

def format_currency_per_m2(value):
    return "—" if pd.isna(value) else format_currency_br(value) + "/m²"

def format_area(value):
    return "—" if pd.isna(value) else format_number(value, 1) + " m²"

def format_percent(value):
    return "—" if pd.isna(value) else format_number(value, 1) + "%"

format_integer_br = format_number

def format_year(value):
    return "—" if pd.isna(value) else str(round(value))

def filter_profile(df, value_range, area_range, construction_range=None, include_missing=True):
    mask = df.base_de_calculo.between(*value_range) & df.area_constr_privativa.between(*area_range)
    if construction_range is not None:
        construction = df.ano_construcao.between(*construction_range).fillna(False)
        if include_missing:
            construction |= df.ano_construcao.isna()
        mask &= construction
    return df.loc[mask].copy()

def summarize(df):
    return df.groupby("bairro_oficial").agg(
        valor_m2=("valor_m2", "median"), base_de_calculo=("base_de_calculo", "median"),
        area=("area_constr_privativa", "median"), construcao=("ano_construcao", "median"),
        registros=("ano", "size"),
    )

def period_change(df, years, minimum):
    names = pd.Index(df.bairro_oficial.unique(), name="bairro_oficial")
    result = pd.Series(float("nan"), index=names, name="variacao")
    if years[0] == years[1]:
        return result
    first = summarize(df.loc[df.ano.eq(years[0])])
    last = summarize(df.loc[df.ano.eq(years[1])])
    valid = first.index.intersection(last.index)
    valid = valid[(first.loc[valid, "registros"] >= minimum) & (last.loc[valid, "registros"] >= minimum)]
    result.loc[valid] = (last.loc[valid, "valor_m2"] / first.loc[valid, "valor_m2"] - 1) * 100
    return result

def neighborhood_metrics(context, filtered, years, minimum):
    result = summarize(filtered).reindex(pd.Index(context.bairro_oficial.unique(), name="bairro_oficial"))
    result["registros"] = result.registros.fillna(0).astype(int)
    result["avaliados"] = context.groupby("bairro_oficial").size()
    result["compatibilidade"] = 100 * result.registros / result.avaliados
    result["variacao"] = period_change(filtered, years, minimum)
    result["suficiente"] = result.registros.ge(minimum)
    return result
