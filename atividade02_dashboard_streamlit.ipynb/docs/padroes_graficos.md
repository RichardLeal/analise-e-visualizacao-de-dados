# Padrão para os gráficos do dashboard

Este documento define como adicionar cada visualização sem misturar cálculo, configuração do gráfico e layout Streamlit.

## Responsabilidades

- `app.py` configura a página, carrega os dados, apresenta os controles, aplica filtros, mostra avisos para seleções sem resultados e organiza a ordem das visualizações.
- `charts.py` contém um construtor independente por gráfico. Cada construtor recebe os dados já filtrados, calcula a agregação necessária e retorna o objeto da biblioteca de visualização.
- `pipeline.py` continua responsável pela preparação compartilhada dos dados. Não duplique o funil em `app.py` ou `charts.py`.

Os construtores não chamam APIs `st.*`, não carregam arquivos e não alteram o DataFrame recebido. A renderização fica em `app.py`, onde cada biblioteca tem sua chamada Streamlit correspondente:

| Objeto retornado | Renderização em `app.py` |
|---|---|
| Figura Plotly | `st.plotly_chart(...)` |
| Gráfico Altair | `st.altair_chart(...)` |
| Mapa Folium | `st_folium(...)` |

## Convenção dos construtores

Use um nome descritivo no formato `build_<visualizacao>`. Passe o DataFrame filtrado como primeiro argumento; parâmetros adicionais, como a métrica escolhida ou limites geográficos, devem ser explícitos.

```python
def build_<visualizacao>(df_filtrado, ...):
    dados_do_grafico = ...
    grafico = ...
    return grafico
```

O primeiro construtor, `build_yearly_median_chart(df)`, em `charts.py`, serve de exemplo completo: agrega a mediana por ano, monta a figura Plotly e a retorna. Em `app.py`, o padrão é:

```python
st.subheader("Título da visualização")
st.plotly_chart(build_yearly_median_chart(df_filtrado), width="stretch")
```

Para os próximos gráficos, mantenha o mesmo fluxo, trocando o construtor e a função de renderização:

```python
st.subheader("Comparação entre bairros")
st.altair_chart(build_neighborhood_median_chart(df_filtrado))

st.subheader("Mapa por bairro")
st_folium(build_price_per_m2_map(df_filtrado, boundaries))
```

Para o mapa de bairros, mantenha cada polígono do GeoJSON mesmo quando não houver transações correspondentes. Use uma cor neutra para áreas sem mediana, inclua a mediana no tooltip, ajuste o enquadramento ao conjunto dos polígonos e destaque o contorno municipal sem mapa-base. Categorias sem geometria, como `JAR ITU SABARA`, não podem ser desenhadas; informe-as separadamente no app em vez de associá-las artificialmente a outro bairro.

## Regras para cada novo gráfico

1. Dê a cada gráfico um construtor próprio em `charts.py`; não acumule lógicas de gráficos diferentes numa única função.
2. Passe os dados já filtrados por `app.py`. Dentro do construtor, faça somente a agregação e a configuração específicas daquela visualização.
3. Use nomes reais das colunas, unidades nos títulos/eixos e tooltips que deixem claro o valor apresentado.
4. Preserve a população analítica definida para a pergunta. Para comparações entre bairros, exclua registros sem bairro; se o total da cidade incluir esses registros, passe esse conjunto separadamente e identifique-o como referência da cidade.
5. Antes de chamar o construtor, `app.py` deve verificar se a seleção contém dados. Se estiver vazia, mostrar `st.warning` e não renderizar o gráfico.
6. Valide os cálculos com `check_data.py` quando houver uma referência numérica e execute a aplicação ou um teste `AppTest` para verificar que o elemento é renderizado sem exceções.

Mantenha os construtores juntos em `charts.py` enquanto o módulo continuar simples. Crie outro módulo apenas se existir uma necessidade concreta de separar uma família de visualizações ou lógica compartilhada.