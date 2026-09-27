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