"""Chart builders for the ITBI dashboard.

Each function builds and returns one visualization. Streamlit rendering stays
in app.py so chart logic can be tested independently.
"""

from collections.abc import Mapping
from typing import Any

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

PORTO_ALEGRE_GREEN = "#1B5E45"
PORTO_ALEGRE_GOLD = "#805D0F"
PORTO_ALEGRE_BLUE = "#3669B2"
PORTO_ALEGRE_WHITE = "#FFFFFF"
PORTO_ALEGRE_RED = "#E40A24"


def build_neighborhood_value_map(
    df: pd.DataFrame, boundaries: Mapping[str, Any]
) -> folium.Map:
    median_by_neighborhood = (
        df.groupby("bairro_oficial", as_index=False)["valor_m2"]
        .median()
        .rename(columns={"valor_m2": "valor_m2_mediano"})
    )
    median_by_name = median_by_neighborhood.set_index("bairro_oficial")["valor_m2_mediano"]

    features = []
    for feature in boundaries["features"]:
        properties = feature["properties"]
        median = median_by_name.get(properties["bairro_oficial"])
        features.append(
            {
                **feature,
                "properties": {
                    **properties,
                    "valor_m2_mediano": float(median) if pd.notna(median) else None,
                },
            }
        )
    geo_data = {**boundaries, "features": features}
    city_outline = unary_union(
        [shape(feature["geometry"]) for feature in features]
    ).boundary
    min_lon, min_lat, max_lon, max_lat = city_outline.bounds

    map_object = folium.Map(
        location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
        zoom_start=10,
        tiles=None,
        control_scale=True,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        max_bounds=True,
    )
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        data=median_by_neighborhood,
        columns=["bairro_oficial", "valor_m2_mediano"],
        key_on="feature.properties.bairro_oficial",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_color="#555555",
        line_weight=0.7,
        line_opacity=0.7,
        nan_fill_color="#d9d9d9",
        nan_fill_opacity=0.8,
        legend_name="Valor mediano por m² (R$/m²)",
        name="Mediana do valor por m²",
    )
    choropleth.geojson.add_child(
        folium.GeoJsonTooltip(
            fields=["bairro_oficial", "valor_m2_mediano"],
            aliases=["Bairro:", "Mediana (R$/m²):"],
            localize=True,
            sticky=False,
        )
    )
    choropleth.add_to(map_object)
    folium.GeoJson(
        {
            "type": "Feature",
            "properties": {"nome": "Limite de Porto Alegre"},
            "geometry": mapping(city_outline),
        },
        style_function=lambda _: {
            "color": "#292929",
            "weight": 2,
            "opacity": 1,
            "fill": False,
        },
        name="Limite de Porto Alegre",
    ).add_to(map_object)
    map_object.fit_bounds(
        [[min_lat, min_lon], [max_lat, max_lon]],
        padding=(8, 8),
    )
    return map_object


def build_neighborhood_record_count_map(
    df: pd.DataFrame, boundaries: Mapping[str, Any]
) -> folium.Map:
    counts_by_neighborhood = (
        df.groupby("bairro_oficial")
        .size()
        .rename("total_registros")
        .reset_index()
    )
    count_by_name = counts_by_neighborhood.set_index("bairro_oficial")["total_registros"]

    features = []
    for feature in boundaries["features"]:
        properties = feature["properties"]
        count = count_by_name.get(properties["bairro_oficial"])
        features.append(
            {
                **feature,
                "properties": {
                    **properties,
                    "total_registros": int(count) if pd.notna(count) else None,
                },
            }
        )
    geo_data = {**boundaries, "features": features}
    city_geometry = unary_union(
        [shape(feature["geometry"]) for feature in features]
    )
    min_lon, min_lat, max_lon, max_lat = city_geometry.bounds
    longitude_margin = (max_lon - min_lon) * 0.25
    latitude_margin = (max_lat - min_lat) * 0.25

    mapped_counts = [
        feature["properties"]["total_registros"]
        for feature in features
        if feature["properties"]["total_registros"] is not None
    ]
    min_count = min(mapped_counts)
    max_count = max(mapped_counts)
    color_scale = folium.LinearColormap(
        colors=[
            "#C77DFF",
            "#E0AAFF",
            "#9D4EDD",
            "#7B2CBF",
            "#5A189A",
            "#3C096C",
            "#240046",
            "#100028",
        ],
        vmin=min_count,
        vmax=max_count,
        caption="Total de registros por bairro",
    )

    def style_neighborhood(feature: Mapping[str, Any]) -> dict[str, Any]:
        count = feature["properties"]["total_registros"]
        if count is None:
            fill_color = PORTO_ALEGRE_WHITE
            fill_opacity = 0.8
        else:
            fill_color = color_scale(count)
            fill_opacity = 0.8
        return {
            "color": "#000000",
            "weight": 1,
            "opacity": 1,
            "fillColor": fill_color,
            "fillOpacity": fill_opacity,
        }

    map_object = folium.Map(
        location=[-30.05, -51.18],
        zoom_start=9,
        tiles=None,
    )
    folium.TileLayer(
        tiles="OpenStreetMap",
        opacity=0.5,
        name="Mapa original",
        control=False,
    ).add_to(map_object)
    folium.GeoJson(
        geo_data,
        name="Total de registros por bairro",
        style_function=style_neighborhood,
        tooltip=folium.GeoJsonTooltip(
            fields=["bairro_oficial", "total_registros"],
            aliases=["Bairro:", "Total de registros:"],
            localize=True,
            sticky=False,
        ),
    ).add_to(map_object)
    color_scale.add_to(map_object)
    map_object.fit_bounds(
        [
            [min_lat - latitude_margin, min_lon - longitude_margin],
            [max_lat + latitude_margin, max_lon + longitude_margin],
        ],
        padding=(8, 8),
    )
    return map_object


def build_explorer_map(stats, boundaries, metric, minimum, focus=None):
    """One map, all official polygons, explicit missing/insufficient states."""
    from metrics import METRICS, format_number, format_currency_br, format_area, format_percent
    from branca.colormap import LinearColormap
    values = stats[metric].where(stats.suficiente)
    if metric == "compatibilidade":
        values = stats[metric].where(stats.avaliados.ge(minimum))
    valid = values.dropna()
    low, high = (float(valid.min()), float(valid.max())) if len(valid) else (0., 1.)
    if metric == "variacao":
        extent = max(abs(low), abs(high), 1)
        low, high = -extent, extent
        colors = ["#2166ac", "#f7f7f7", "#b2182b"]
    else:
        colors = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
        if metric == "registros":
            colors = ["#E0AAFF", "#9D4EDD", "#5A189A", "#100028"]
    scale = LinearColormap(colors, vmin=low, vmax=high if high > low else low + 1, caption=METRICS[metric])
    scale.width = 300
    features = []
    for feature in boundaries["features"]:
        name = feature["properties"]["bairro_oficial"]
        row = stats.loc[name] if name in stats.index else None
        value = values.get(name)
        status = "Dados suficientes" if pd.notna(value) else "Sem dados ou dados insuficientes para esta métrica"
        props = {"bairro_oficial": name, "estado": status,
                 "cor": scale(float(value)) if pd.notna(value) else "#d9d9d9"}
        for key, formatter in [("valor_m2", format_currency_br), ("base_de_calculo", format_currency_br),
                               ("area", format_area), ("registros", format_number),
                               ("avaliados", format_number), ("compatibilidade", format_percent), ("variacao", format_percent)]:
            props[key] = formatter(row[key]) if row is not None else "—"
        features.append({**feature, "properties": props})
    m = folium.Map(location=[-30.08, -51.17], zoom_start=11, tiles=None, control_scale=True,
                   zoom_snap=0.1, zoom_delta=0.5)
    folium.TileLayer("OpenStreetMap", opacity=0.5, control=False).add_to(m)
    layer = folium.GeoJson({**boundaries, "features": features},
        style_function=lambda f: {"fillColor": f["properties"]["cor"], "fillOpacity": .8,
            "color": "#3669B2" if f["properties"]["bairro_oficial"] == focus else "#555555",
            "weight": 3 if f["properties"]["bairro_oficial"] == focus else .7},
        highlight_function=lambda _: {"weight": 3, "color": "#3669B2"},
        tooltip=folium.GeoJsonTooltip(
            fields=["bairro_oficial", "estado", "valor_m2", "base_de_calculo", "area", "registros", "avaliados", "compatibilidade", "variacao"],
            aliases=["Bairro", "Cobertura", "Valor/m² mediano (R$/m²)", "Base de cálculo mediana", "Área mediana", "Registros compatíveis", "Registros avaliados", "Compatibilidade histórica", "Variação no período"], sticky=False))
    layer.add_to(m)
    m.fit_bounds(layer.get_bounds())
    if len(valid):
        scale.add_to(m)
    return m


def build_yearly_median_chart(df, metric="base_de_calculo", neighborhoods=(), city_df=None, years=None, minimum=1):
    from metrics import METRICS, format_currency_br, format_number
    city_df = df if city_df is None else city_df
    years = years or (int(city_df.ano.min()), int(city_df.ano.max()))
    fig = go.Figure()
    series = [("Porto Alegre", city_df)] + [(n, df.loc[df.bairro_oficial.eq(n)]) for n in neighborhoods]
    colors = ["#858d99", PORTO_ALEGRE_RED, PORTO_ALEGRE_BLUE, PORTO_ALEGRE_GREEN, PORTO_ALEGRE_GOLD]
    for i, (name, frame) in enumerate(series):
        grouped = frame.groupby("ano")[metric].agg(["median", "size"]).reindex(range(years[0], years[1] + 1))
        grouped.loc[grouped["size"].fillna(0).lt(minimum), "median"] = float("nan")
        fig.add_trace(go.Scatter(x=grouped.index, y=grouped["median"], name=name, mode="lines+markers", connectgaps=False,
            line={"color": colors[i % len(colors)], "dash": "dash" if i == 0 else "solid"},
            customdata=[[format_currency_br(v), format_number(n)] for v, n in zip(grouped["median"], grouped["size"])],
            hovertemplate="Ano: %{x}<br>Mediana: %{customdata[0]}<br>Registros: %{customdata[1]}<extra>%{fullData.name}</extra>"))
    fig.update_layout(xaxis_title="Ano da base", yaxis_title=METRICS[metric], height=360,
                      margin=dict(l=10,r=10,t=20,b=10), legend=dict(orientation="h", y=1.15), separators=",.", template="plotly_white")
    fig.update_xaxes(dtick=1)
    return fig


def build_neighborhood_bars(stats, metric="base_de_calculo", focus=None, ascending=False):
    import altair as alt
    from metrics import METRICS, format_currency_br, format_number
    data = stats.loc[stats.suficiente].reset_index().copy()
    data["mediana_formatada"] = data[metric].map(format_currency_br)
    data["registros_formatados"] = data.registros.map(format_number)
    return alt.Chart(data).mark_bar().encode(
        x=alt.X(f"{metric}:Q", title=METRICS[metric]),
        y=alt.Y("bairro_oficial:N", sort=alt.SortField(field=metric, order="ascending" if ascending else "descending"), title=None),
        color=alt.condition(alt.datum.bairro_oficial == (focus or ""), alt.value(PORTO_ALEGRE_RED), alt.value(PORTO_ALEGRE_BLUE)),
        tooltip=[alt.Tooltip("bairro_oficial:N", title="Bairro"), alt.Tooltip("mediana_formatada:N", title=METRICS[metric]), alt.Tooltip("registros_formatados:N", title="Registros")],
    ).properties(height=max(180, len(data)*23)).configure_view(stroke=None)


def build_neighborhood_scatter(stats, focus=None):
    from metrics import format_currency_br, format_area, format_number
    data = stats.loc[stats.suficiente].reset_index().copy()
    data["destaque"] = data.bairro_oficial.eq(focus)
    data["rotulo"] = data.bairro_oficial.where(data.destaque, "")
    for key, formatter in [("valor_m2", format_currency_br), ("base_de_calculo", format_currency_br), ("area", format_area), ("registros", format_number)]:
        data[key+"_texto"] = data[key].map(formatter)
    fig = px.scatter(data, x="valor_m2", y="registros", text="rotulo", color="destaque",
        color_discrete_map={False: "#a6adb7", True: PORTO_ALEGRE_RED},
        custom_data=["bairro_oficial", "valor_m2_texto", "base_de_calculo_texto", "area_texto", "registros_texto"],
        labels={"valor_m2": "Valor/m² mediano (R$/m²)", "registros": "Número de registros"})
    fig.update_traces(marker_size=10, textposition="top center", hovertemplate="%{customdata[0]}<br>Valor/m²: %{customdata[1]}<br>Base: %{customdata[2]}<br>Área: %{customdata[3]}<br>Registros: %{customdata[4]}<extra></extra>")
    fig.update_layout(showlegend=False, height=360, template="plotly_white", separators=",.", margin=dict(l=10,r=10,t=20,b=10))
    return fig
