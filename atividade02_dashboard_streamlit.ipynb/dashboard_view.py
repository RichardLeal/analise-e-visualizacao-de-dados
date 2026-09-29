"""Build the desktop component payload using the existing analytical functions."""
import json
import pandas as pd
from charts import build_explorer_map, build_yearly_median_chart, build_neighborhood_scatter, build_neighborhood_bars
from metrics import METRICS, filter_profile, neighborhood_metrics, format_currency_br, format_currency_per_m2, format_area, format_percent, format_integer_br, format_year


def default_state(df):
    return dict(years=[int(df.ano.min()), int(df.ano.max())],
                value=[float(df.base_de_calculo.min()), float(df.base_de_calculo.max())],
                area=[float(df.area_constr_privativa.min()), float(df.area_constr_privativa.max())],
                construction=[int(df.ano_construcao.min()), int(df.ano_construcao.max())],
                construction_active=False, include_missing=True, neighborhoods=[], minimum=100,
                metric="valor_m2", focus="PETRÓPOLIS", comparison=[], line_metric="base_de_calculo",
                bar_metric="base_de_calculo", ascending=False)


def build_payload(df, boundaries, state):
    defaults = default_state(df)
    state = {**defaults, **state}
    names = sorted(df.bairro_oficial.unique())
    for key in ("neighborhoods", "comparison"):
        state[key] = [n for n in state[key] if n in names]
    state["comparison"] = state["comparison"][:4]
    years = state["years"]
    minimum = max(1, int(state["minimum"]))
    period = df.loc[df.ano.between(*years)]
    context = period.loc[period.bairro_oficial.isin(state["neighborhoods"])] if state["neighborhoods"] else period
    city = filter_profile(period, state["value"], state["area"],
                          state["construction"] if state["construction_active"] else None, state["include_missing"])
    filtered = city.loc[city.bairro_oficial.isin(state["neighborhoods"])] if state["neighborhoods"] else city
    stats = neighborhood_metrics(context, filtered, years, minimum)
    options = sorted(stats.index)
    if state["focus"] not in options:
        state["focus"] = options[0] if options else None
    state["comparison"] = [n for n in state["comparison"] if n in options]
    focus = state["focus"]
    row = stats.loc[focus] if focus else None
    kpis = []
    for label, key, source, fmt in [
        ("Valor/m² mediano", "valor_m2", "valor_m2", format_currency_per_m2),
        ("Base de cálculo mediana", "base_de_calculo", "base_de_calculo", format_currency_br),
        ("Área privativa mediana", "area", "area_constr_privativa", format_area)]:
        value = row[key] if row is not None and row.suficiente else float("nan")
        ref = city[source].median()
        delta = (value/ref-1)*100 if ref > 0 else float("nan")
        kpis.append(dict(label=label, value=fmt(value), delta=format_percent(delta), positive=bool(pd.notna(delta) and delta>0)))
    count = int(row.registros) if row is not None else 0
    kpis.append(dict(label="Número de registros", value=format_integer_br(count),
                     delta=format_percent(count/len(city)*100) if len(city) else "—", share=True, positive=False))
    compared = state["comparison"] or ([focus] if focus else [])
    table = stats.reindex(compared).copy()
    table.loc[~table.suficiente.fillna(False), ["valor_m2", "base_de_calculo", "area", "construcao", "variacao"]] = float("nan")
    rows = []
    for key, label, fmt in [("valor_m2", "Valor/m² (R$/m²)", format_currency_per_m2),
        ("base_de_calculo", "Base de cálculo (R$)", format_currency_br), ("area", "Área privativa", format_area),
        ("construcao", "Ano de construção", format_year), ("registros", "Registros", format_integer_br),
        ("variacao", "Variação no período", format_percent)]:
        rows.append(dict(label=label, values=[fmt(v) for v in table[key]]))
    line_names = list(dict.fromkeys(([focus] if focus else []) + state["comparison"]))[:4]
    line = build_yearly_median_chart(filtered, state["line_metric"], line_names, city, years, minimum)
    scatter = build_neighborhood_scatter(stats, focus)
    for figure in (line, scatter):
        figure.update_layout(height=None, autosize=True, font=dict(size=11, color="#203858"),
            margin=dict(l=58,r=15,t=8,b=32), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
        figure.update_yaxes(nticks=4, title_font_size=10, tickfont_size=10, automargin=True)
        figure.update_xaxes(nticks=5, title_font_size=10, tickfont_size=10, automargin=True)
    line.update_layout(legend=dict(orientation="h", y=1.02, yanchor="bottom", font=dict(size=10)), margin_t=27)
    eligible = stats.loc[stats.suficiente].sort_values(state["bar_metric"], ascending=state["ascending"])
    # Eight rows maximum; the frontend reduces the count to fit smaller panels.
    bars = build_neighborhood_bars(eligible.head(8), state["bar_metric"], focus, state["ascending"]).to_dict()
    m = build_explorer_map(stats, boundaries, state["metric"], minimum, focus)
    # Folium already generates a 100%-height Leaflet map. Invalidate on iframe resize.
    m.get_root().script.add_child(__import__("branca").element.Element(
        f"new ResizeObserver(() => {{ {m.get_name()}.invalidateSize(); "
        f"{m.get_name()}.fitBounds({json.dumps(m.get_bounds())}, {{padding:[4,4]}}); }}).observe(document.body);"))
    # Keep hover content inside the map iframe, including polygons near its edges.
    m.get_root().script.add_child(__import__("branca").element.Element(
        f"setTimeout(() => {m.get_name()}.on('tooltipopen', event => requestAnimationFrame(() => {{"
        "const el=event.tooltip.getElement(); el.style.marginTop='0px'; el.style.marginLeft='0px';"
        "const r=el.getBoundingClientRect();"
        "const top=Math.min(55,Math.max(6,innerHeight-r.height-6));"
        "el.style.marginTop=Math.max(top-r.top,Math.min(0,innerHeight-6-r.bottom))+'px';"
        "el.style.marginLeft=Math.max(6-r.left,Math.min(0,innerWidth-6-r.right))+'px';"
        "})),0);"))
    map_html = m.get_root().render()
    decimals = 1 if state["metric"] in ("compatibilidade", "variacao") else 0
    map_html = map_html.replace('.tickSize(1)', '.tickSize(1).tickFormat(value => '
        f'new Intl.NumberFormat("pt-BR", {{maximumFractionDigits:{decimals}}}).format(value))')
    unmapped = int((~filtered.tem_poligono).sum())
    note = f"{format_integer_br(len(filtered))} compatibles / {format_integer_br(len(context))} avaliados · {years[0]}–{years[1]}"
    note = note.replace("compatibles", "compatíveis")
    metric_note = "Cinza: sem dados ou amostra insuficiente. Valores fiscais, não preços de mercado."
    if state["metric"] == "compatibilidade":
        metric_note = "Compatíveis ÷ avaliados antes dos filtros de perfil. Mínimo aplicado ao denominador."
    elif state["metric"] == "variacao":
        metric_note = "Selecione pelo menos dois anos." if years[0] == years[1] else f"Variação nominal {years[0]}–{years[1]}; mínimo {minimum} em cada extremo."
    if unmapped:
        metric_note += f" {unmapped} registros sem polígono permanecem nas tabelas."
    return dict(state=state, defaults=defaults, names=names, options=options, metrics=METRICS,
                total=format_integer_br(len(df)), note=note, metric_note=metric_note,
                empty=filtered.empty, kpis=kpis, focus_count=count,
                focus_sufficient=bool(row is not None and row.suficiente),
                missing_construction=format_integer_br(df.ano_construcao.isna().sum()),
                map_html=map_html, line=json.loads(line.to_json()), scatter=json.loads(scatter.to_json()),
                bars=bars, eligible_count=len(eligible), compared=compared, table=rows)
