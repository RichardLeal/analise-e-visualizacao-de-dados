# Entrega — Visão geral do Mapa Imobiliário POA

## Arquivos

- `dashboard/index.html`: nova estrutura da Visão geral e destino da comparação.
- `dashboard/dashboard.css`: composição da referência, responsividade e estilos por view.
- `dashboard/dashboard.js`: navegação, seleção integrada, controles, resize e transferência do foco.
- `dashboard_view.py`: estado inicial e payload dedicado, com cálculos exclusivamente em Python.
- `charts.py`: adaptação do mapa existente para tooltip simples e seleção por mensagem do iframe.
- `test_dashboard.py`: testes da nova experiência, mantendo as referências existentes.
- `visual_check.py`: verificações e capturas de ambas as páginas nas três resoluções desktop.
- `README.md`, `tasks.md`, `docs/escopo.md`, `docs/padroes_de_design.md`: arquitetura e uso atualizados.
- `atividade02_dashboard_streamlit.ipynb`: apenas uma célula final de registro, preservando análises e saídas.

`app.py`, pipeline, dados e geometria oficial foram preservados.

## Navegação

Abertura em **Visão geral**; views reais para **Análise de bairros** e **Comparação**.
**Sobre os dados** mantém o modal acessível em qualquer página. O período é compartilhado.
Mínimo, foco e ordenação da Visão geral são independentes dos filtros analíticos.

## Perguntas acadêmicas

| Pergunta | Implementação |
|---|---|
| P1 — evolução entre 2020 e 2025 | Mediana de `base_de_calculo` por ano, Plotly, linha da cidade e bairro opcional; tooltip com contagem. |
| P2 — maiores e menores medianas | Elegibilidade pelo mínimo, ordenação pela mediana de `base_de_calculo`, barras Plotly com 5 ou 10 bairros. |
| P3 — variação entre bairros | Mediana de `valor_m2`, Folium, YlOrRd, 94 polígonos oficiais, amostra insuficiente em cinza. |

Nenhum número da imagem foi fixado no código. KPIs usam todos os registros do período.
Os deltas comparam as medianas anuais dos extremos; valores fiscais nominais não são necessariamente
preços de mercado. JAR ITU SABARA segue sem geometria artificial.

## Visão geral → análise

Mapa, barras e seletor alteram o foco. O resumo apresenta medianas e registros do bairro.
**Analisar este bairro →** leva bairro e período para a análise e reinicia os filtros avançados.
A troca comum pelos itens de navegação mantém os filtros e a comparação atuais.

## Execução

Na pasta `atividade02_dashboard_streamlit.ipynb`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
.\.venv\Scripts\python.exe check_data.py
.\.venv\Scripts\python.exe test_dashboard.py
.\.venv\Scripts\python.exe visual_check.py
```

Para validar outra porta, defina `$env:DASHBOARD_URL='http://localhost:8502'`.

## Limitações

- Mapa-base e bibliotecas do Folium dependem de rede, como na implementação anterior.
- A Visão geral permite rolagem vertical; a análise continua cabendo em uma tela desktop.
- O seletor permite acesso por teclado ao foco, além do clique em mapa/barras.
- A instalação local de Streamlit estava incompleta por limite de caminho do Windows; foi restaurada.
- Não foi feita uma revisão específica em celular, fora das três resoluções desktop solicitadas.

## Validação e screenshots

- `check_data.py`: passou; funil, medianas de referência e Parquet preservados.
- `test_dashboard.py`: 9 testes passaram, incluindo os 5 existentes.
- `visual_check.py --screenshots-only`: passou nas três resoluções (1366×768, 1536×864, 1920×1080).
- Capturas completas: [1366×768](../artifacts/visual/overview-content-1366x768.png),
  [1536×864](../artifacts/visual/overview-content-1536x864.png),
  [1920×1080](../artifacts/visual/overview-content-1920x1080.png).
- Petrópolis selecionado: [1366×768](../artifacts/visual/overview-selected-1366x768.png),
  [1536×864](../artifacts/visual/overview-selected-1536x864.png),
  [1920×1080](../artifacts/visual/overview-selected-1920x1080.png).
- As capturas completas mantêm a largura testada e ampliam a altura da captura para incluir
  o conteúdo rolável; a verificação de layout usa os viewports originais.
- Evidências da análise, tooltips e seletores também estão em `artifacts/visual/`.

- `visual_check.py` completo: passou nas três resoluções, incluindo clique nas barras, mensagem do mapa, seleção, aprofundamento, retorno, comparação, filtros avançados, mínimos extremos e metodologia.
- `git diff --check`: passou.
