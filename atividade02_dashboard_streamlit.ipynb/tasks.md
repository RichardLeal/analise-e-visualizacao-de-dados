# Tarefas — Atividade 02 (Dashboard Streamlit)

**Prazo:** 29/09/2026 às 19:00, no Moodle ("Tarefa 02 - Entrega").
**Escopo detalhado:** [docs/escopo.md](docs/escopo.md).

Legenda: `[x]` feito · `[ ]` a fazer. Preencham o responsável de cada tarefa.

## Preparação (sáb 26/09)

- [ ] **T01 — Validar o escopo.** Responsável: _grupo_
  A proposta está em `docs/escopo.md`: público, perguntas, gráficos, bibliotecas e filtros. Falta o grupo decidir:
  - [ ] Registros com percentual transmitido < 100% (3.646, ou 3,1%): manter e citar como limitação, ou excluir?
  - [ ] "JAR ITU SABARA" (134 registros, fica fora do mapa): manter nos outros gráficos ou excluir?
  - [ ] Incluir o filtro de faixa de área privativa (m²)?
  - [ ] Nome dos bairros na tela: oficial com acento ou o do ITBI?
- [x] **T02 — Estrutura do projeto.** Pasta desta atividade com `app.py`, `charts.py`, `pipeline.py`, `geo.py`, `prepare_data.py`, `check_data.py`, `data/`, `docs/`, `requirements.txt`, `README.md`.
- [x] **T03 — Preparação dos dados.** O `prepare_data.py` aplica o funil da Atividade 01 e gera `data/apartamentos_itbi_poa.parquet` (116.198 apartamentos).
- [x] **T04 — Conferência contra a Atividade 01.** O `check_data.py` bate o funil, as medianas por ano e as medianas por bairro. Todos os itens passam.
- [x] **T05 — Mapa dos bairros.** O `data/bairros_poa.geojson` tem 94 bairros oficiais; 84 dos 85 bairros da base aparecem no mapa.

## Dashboard (dom 27/09 a seg 28/09)

Só começar depois do T01.

- [ ] **T06 — Esqueleto do app.** Responsável: ___
  Página com título e texto de contexto para o público. O texto explica em uma frase o que são "mediana" e "base de cálculo". O rodapé mostra fonte e licença, copiadas do README.
- [ ] **T07 — Filtros na sidebar.** Responsável: ___
  - Período, com `st.slider` de faixa.
  - Bairros, com `st.multiselect`.
  - Métrica valor total (R$) ou valor/m² (R$/m²), com `st.radio`.
  - Mínimo de registros por bairro, com padrão 100.

  Quando a seleção ficar vazia, mostrar `st.warning` e não desenhar os gráficos.
- [ ] **T08 — Indicadores no topo.** Responsável: ___
  Três `st.metric`: número de apartamentos, valor mediano e valor/m² mediano da seleção.
- [ ] **T09 — Gráfico 1 (P1), Plotly.** Responsável: ___
  Linha com a mediana por ano, com a cidade como referência (tracejada) e uma linha por bairro selecionado. Segue o filtro de métrica.
  Implementar em `charts.py` como construtor que recebe os dados filtrados e retorna a figura; `app.py` renderiza a figura.
- [ ] **T10 — Gráfico 2 (P2/P3), Altair.** Responsável: ___
  Barras horizontais ordenadas com a mediana por bairro, respeitando o mínimo de registros. Tooltip com o número de registros; bairros selecionados em destaque.
  Implementar em `charts.py` como construtor que recebe os dados filtrados e retorna o gráfico Altair; `app.py` renderiza o gráfico.
- [x] **T11 — Gráfico 3 (P3), Folium.** Responsável: ___
  Mapa coroplético com o valor/m² mediano por `bairro_oficial` (`folium.Choropleth` + `streamlit-folium`). Bairros sem dados ficam em cinza.
  Implementar em `charts.py` como construtor que recebe os dados filtrados e os limites geográficos e retorna o mapa; `app.py` o renderiza com `st_folium`.
  Seguir [`docs/padroes_de-design.md`](docs/padroes_de-design.md) para o padrão visual e a separação entre cálculo, construção e renderização.
  O mapa mostra os 94 polígonos oficiais; `JAR ITU SABARA` não possui polígono e é informado separadamente.
- [ ] **T12 — Textos de apoio.** Responsável: ___
  Eixos com unidade (R$, R$/m²) e uma ou duas frases de leitura abaixo de cada gráfico. Incluir o aviso de que a base de cálculo é a base fiscal do imposto, e não o preço de mercado.

## Fechamento (ter 29/09, até ~17h)

- [ ] **T13 — README final.** Responsável: ___
  Revisar a instalação e a execução, e colocar um print do dashboard. As versões já estão fixadas no `requirements.txt`.
- [ ] **T14 — Teste de reprodução.** Responsável: ___ (alguém que **não** escreveu o app)
  Clonar o repositório, criar a venv e rodar só seguindo o README, numa máquina ou venv limpa.
- [ ] **T15 — Teste dos filtros.** Responsável: ___
  - Testar 1 ano, 1 bairro, seleção vazia, todos os bairros e mínimo de registros alto.
  - Conferir 2 ou 3 números com a Atividade 01. Exemplo: mediana de 2025 = R$ 240.000.
- [ ] **T16 — Registro do grupo no notebook.** Responsável: ___
  Preencher todos os campos do final de `atividade02_dashboard_streamlit.ipynb`:
  - Integrantes.
  - Perguntas contempladas.
  - Gráficos e bibliotecas, com a justificativa (usar a tabela do escopo).
  - Exemplo de uso dos filtros.
  - Um resultado e uma limitação.
  - Mudanças em relação à Atividade 01 (seção "Mudanças" do escopo).
  - Uso de IA e referências.
- [ ] **T17 — Montar e enviar o ZIP.** Responsável: ___
  - O ZIP leva esta pasta, **sem** `.venv/`, `__pycache__/` e `data/raw/`.
  - Conferir que o ZIP abre e tem `app.py`, `requirements.txt`, `README.md`, `data/` e o notebook.
  - Enviar no Moodle.

## Opcional

- [x] Mapa adicional: total de registros por bairro em roxo, com mapa-base a 50%, bairros de menor volume até 50% de opacidade e limites pretos.
- [ ] Publicar no Streamlit Community Cloud e colocar o link no README.
- [ ] Gráfico 5: distribuição do valor/m² (boxplot ou histograma) nos bairros selecionados.
