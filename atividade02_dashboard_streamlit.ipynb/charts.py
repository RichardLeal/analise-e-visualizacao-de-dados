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


def build_yearly_median_chart(df: pd.DataFrame) -> go.Figure:
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
        color_discrete_sequence=[PORTO_ALEGRE_GREEN],
        title="Valor mediano dos apartamentos por ano",
        labels={
            "ano": "Ano",
            "base_de_calculo": "Base de cálculo mediana (R$)",
        },
    )
    fig.update_traces(
        line={"color": PORTO_ALEGRE_GREEN, "width": 3},
        marker={
            "color": PORTO_ALEGRE_GOLD,
            "size": 9,
            "line": {"color": PORTO_ALEGRE_WHITE, "width": 1.5},
        },
    )
    fig.update_layout(
        paper_bgcolor=PORTO_ALEGRE_WHITE,
        plot_bgcolor=PORTO_ALEGRE_WHITE,
        font={"color": "#252B28"},
        title={"font": {"color": PORTO_ALEGRE_BLUE}},
        hoverlabel={
            "bgcolor": PORTO_ALEGRE_WHITE,
            "bordercolor": PORTO_ALEGRE_RED,
            "font": {"color": "#252B28"},
        },
    )
    fig.update_xaxes(showgrid=False, linecolor="#D7DED8")
    fig.update_yaxes(
        tickprefix="R$ ",
        tickformat=",.0f",
        showgrid=True,
        gridcolor="#E5EAE6",
        zeroline=False,
    )
    fig.update_traces(
        hovertemplate="Ano: %{x}<br>Base de cálculo mediana: R$ %{y:,.0f}<extra></extra>"
    )
    return fig


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