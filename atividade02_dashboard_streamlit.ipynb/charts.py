"""Chart builders for the ITBI dashboard.

Each function builds and returns one visualization. Streamlit rendering stays
in app.py so chart logic can be tested independently.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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