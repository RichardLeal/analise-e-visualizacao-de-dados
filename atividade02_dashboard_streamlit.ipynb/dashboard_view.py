"""Build the desktop component payload using the existing analytical functions."""
import json
import pandas as pd
from charts import build_explorer_map, build_yearly_median_chart, build_neighborhood_scatter, build_neighborhood_bars
from metrics import METRICS, filter_profile, neighborhood_metrics, format_currency_br, format_currency_per_m2, format_area, format_percent, format_integer_br, format_year


def default_state(df):
    return dict(view="overview", overview=dict(minimum=100, focus=None, ascending=False, count=10),
                years=[int(df.ano.min()), int(df.ano.max())],
                value=[float(df.base_de_calculo.min()), float(df.base_de_calculo.max())],
                area=[float(df.area_constr_privativa.min()), float(df.area_constr_privativa.max())],
                construction=[int(df.ano_construcao.min()), int(df.ano_construcao.max())],
                construction_active=False, include_missing=True, neighborhoods=[], minimum=100,
                metric="valor_m2", focus="PETRÓPOLIS", comparison=[], line_metric="base_de_calculo",
                bar_metric="base_de_calculo", ascending=False)


def build_payload(df, boundaries, state):
    defaults = default_state(df)
    state = {**defaults, **state}
    state["view"] = state["view"] if state["view"] in ("overview", "analysis", "comparison") else "overview"
    state["overview"] = {**defaults["overview"], **state.get("overview", {})}
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
    overview = build_overview(df, boundaries, state)
    return dict(state=state, defaults=defaults, names=names, options=options, metrics=METRICS, overview=overview,
                total=format_integer_br(len(df)), note=note, metric_note=metric_note,
                empty=filtered.empty, kpis=kpis, focus_count=count,
                focus_sufficient=bool(row is not None and row.suficiente),
                missing_construction=format_integer_br(df.ano_construcao.isna().sum()),
                map_html=map_html, line=json.loads(line.to_json()), scatter=json.loads(scatter.to_json()),
                bars=bars, eligible_count=len(eligible), compared=compared, table=rows)

def build_overview(df, boundaries, state):
    """City panorama: only period and overview sample threshold apply."""
    from charts import build_overview_map
    import plotly.graph_objects as go
    settings = state['overview']
    years = state['years']
    minimum = max(1, int(settings['minimum']))
    settings['minimum'] = minimum
    settings['count'] = 5 if settings['count'] == 5 else 10
    period = df.loc[df.ano.between(*years)]
    stats = neighborhood_metrics(period, period, years, minimum)
    focus = settings['focus'] if settings['focus'] in stats.index else None
    settings['focus'] = focus
    eligible = stats.loc[stats.suficiente].sort_values('base_de_calculo', ascending=settings['ascending'], kind='stable')
    ranked = eligible.head(settings['count'])
    # The minimum controls P2/P3, never the city reference in P1.
    line = build_yearly_median_chart(period, 'base_de_calculo', [focus] if focus else [], period, years, 1)
    if focus:
        line.data[1].line.color = '#3276cc'
    bars = go.Figure(go.Bar(
        x=ranked.base_de_calculo.tolist(), y=ranked.index.tolist(), orientation='h',
        marker_color=['#bc1636' if name == focus else '#477fc4' for name in ranked.index],
        text=[format_currency_br(v) for v in ranked.base_de_calculo], textposition='outside', cliponaxis=False,
        customdata=[[name, format_integer_br(row.registros)] for name, row in ranked.iterrows()],
        hovertemplate='%{y}<br>Base de cálculo: %{text}<br>Registros: %{customdata[1]}<extra></extra>'))
    bars.update_layout(template='plotly_white', separators=',.', showlegend=False,
                       xaxis_title='Base de cálculo mediana (R$)', yaxis=dict(autorange='reversed'))
    if ranked.empty:
        bars.add_annotation(text='Nenhum bairro atende ao mínimo de registros.', x=.5, y=.5,
                            xref='paper', yref='paper', showarrow=False)
    for figure in (line, bars):
        figure.update_layout(height=None, autosize=True, font=dict(size=11, color='#203858'),
                             margin=dict(l=65, r=35, t=12, b=40), paper_bgcolor='white', plot_bgcolor='white')
        figure.update_xaxes(gridcolor='#edf2f8', automargin=True)
        figure.update_yaxes(gridcolor='#edf2f8', automargin=True)
    line.update_layout(yaxis_title='R$', xaxis_title='Ano', legend=dict(orientation='h', y=1.02, yanchor='bottom'), margin_t=30)
    bars.update_layout(margin=dict(l=130, r=95, t=6, b=40))
    bars.update_xaxes(tickformat='~s')
    summary = dict(total=int(len(period)), base_de_calculo=None if period.empty else float(period.base_de_calculo.median()),
                   valor_m2=None if period.empty else float(period.valor_m2.median()))
    kpis = []
    for key, label, fmt in [('total', 'Total de registros', format_integer_br),
                            ('base_de_calculo', 'Base de cálculo mediana', format_currency_br),
                            ('valor_m2', 'Valor por m² mediano', format_currency_per_m2)]:
        note = f'registros de apartamentos · {years[0]}–{years[1]}'
        if key != 'total':
            first = period.loc[period.ano.eq(years[0]), key].median()
            last = period.loc[period.ano.eq(years[1]), key].median()
            delta = (last / first - 1) * 100 if first > 0 and years[0] != years[1] else float('nan')
            note = ('+' if pd.notna(delta) and delta > 0 else '') + format_percent(delta) + f' · {years[1]} vs. {years[0]}'
            if years[0] == years[1]:
                note = 'Mediana no ano selecionado'
        kpis.append(dict(label=label, value=fmt(summary[key]), note=note))
    row = stats.loc[focus] if focus else None
    sufficient = row is not None and bool(row.suficiente)
    selected = dict(name=focus, sufficient=sufficient,
                    valor_m2=format_currency_per_m2(row.valor_m2 if sufficient else float('nan')),
                    base_de_calculo=format_currency_br(row.base_de_calculo if sufficient else float('nan')),
                    registros=format_integer_br(row.registros if row is not None else 0),
                    mapped=bool(focus and focus in {f['properties']['bairro_oficial'] for f in boundaries['features']}))
    m = build_overview_map(stats, boundaries, minimum, focus)
    map_html = m.get_root().render().replace(
        '.tickSize(1)', '.tickSize(1).tickFormat(value => new Intl.NumberFormat("pt-BR", {maximumFractionDigits:0}).format(value))')
    return dict(summary=summary, kpis=kpis, line=json.loads(line.to_json()), bars=json.loads(bars.to_json()),
                ranking=[dict(bairro=name, registros=int(row.registros), base_de_calculo=float(row.base_de_calculo)) for name, row in ranked.iterrows()],
                map_html=map_html, focus=selected, eligible_count=len(eligible),
                note='Os valores representam a base fiscal do ITBI e são utilizados como aproximação analítica; não equivalem necessariamente ao preço de mercado.')
