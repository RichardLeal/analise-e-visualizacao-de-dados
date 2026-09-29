# Mapa Imobiliário POA — registros de ITBI (2020–2025)

## Dashboard desktop em uma tela

A interface usa um mapa vertical à esquerda, ocupando as duas primeiras linhas.
À direita, os indicadores ficam acima dos gráficos altos de evolução e dispersão.
Barras e comparação ocupam a base. As linhas usam 22%, 48% e 30% da altura útil;
cabeçalho e margens são descontados de `100dvh`. Não usa escala da interface nem
overflow oculto para cortar conteúdo. Em 1366×768, os dois gráficos principais têm
328 px de altura de painel, contra 171 px na composição horizontal anterior.

O ranking mostra de 5 a 8 bairros conforme a altura, informando o limite; alterne
Maiores/Menores para investigar os extremos. Comparação aceita quatro bairros. Seletores
múltiplos e metodologia abrem em diálogos, sem expandir a página principal. A navegação
destaca os painéis que já estão visíveis. O brasão real ocupa o lugar da foto da referência:
não há fotografias de bairros no projeto.

### Arquivos do layout

- `dashboard/index.html`, `dashboard.css`, `dashboard.js`: componente local com grade,
  controles HTML e gráficos ajustados às dimensões reais dos contêineres.
- `dashboard_view.py`: adapta os cálculos Python existentes ao componente.
- `dashboard/vendor/`: Plotly e Vega locais; execução não requer Node/npm.
- `visual_check.py`: verificação no Chrome isolado, zoom 100%, medições e capturas.
- `artifacts/visual/`: evidências das três resoluções, seletores e comparação.

### Reproduzir a verificação visual

Com Google Chrome instalado e o servidor ativo em `localhost:8501`:

```bash
python -m pip install playwright
python visual_check.py
```

Playwright é uma dependência de desenvolvimento. O teste usa perfil temporário e escala
de dispositivo 1. Confere 1366×768, 1536×864 e 1920×1080; dimensões da página/cartões;
tooltip do mapa; filtros; quatro bairros; ausentes; bairro sem geometria e mínimo alto.
Abaixo de 1050 px de largura, permite rolagem para preservar a leitura; esse modo fica
fora do requisito desktop. Folium/Leaflet e os tiles OpenStreetMap usam recursos de rede.

Capturas: [1366×768](artifacts/visual/dashboard-1366x768.png),
[1536×864](artifacts/visual/dashboard-1536x864.png),
[1920×1080](artifacts/visual/dashboard-1920x1080.png).

IA001 — Análise e Visualização de Dados (Especialização em IA Avançada, INF-UFRGS). Atividade 02: dashboard interativo em Streamlit.

Grupo: Giulia Giozza, Richard Ramos, Eduardo Mello.

## Estrutura

Todos os comandos abaixo são executados dentro desta pasta (`atividade02_dashboard_streamlit.ipynb/`).

| Arquivo | O que é |
|---|---|
| `app.py` | Aplicação Streamlit |
| `charts.py` | Construtores dos gráficos; um por visualização |
| `.streamlit/config.toml` | Tema visual do dashboard inspirado na bandeira e no brasão de Porto Alegre |
| `pipeline.py` | Carga da API e funil de preparação (mesmas regras da Atividade 01) |
| `geo.py` | Limites oficiais dos bairros e casamento com os nomes do ITBI |
| `prepare_data.py` | Gera os arquivos em `data/` |
| `check_data.py` | Confere os dados contra os números entregues na Atividade 01 |
| `data/apartamentos_itbi_poa.parquet` | Base analítica (um apartamento por linha) |
| `data/bairros_poa.geojson` | Limites dos bairros (WGS84) |
| `data/bairros_correspondencia.csv` | Nome no ITBI → nome oficial |
| `data/funil.csv` | Registros restantes após cada etapa |
| `docs/escopo.md` | Público, perguntas, gráficos e filtros do dashboard |
| `docs/padroes_de_design.md` | Padrão de design, interação e implementação das visualizações |
| `tasks.md` | Tarefas do grupo e status |
| `atividade02_dashboard_streamlit.ipynb` | Notebook da atividade (com o Registro do grupo) |

## Instalação

Requer Python 3.11 ou superior.

Instale as dependências a partir da pasta do projeto (atividade02_dashboard_streamlit.ipynb):
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Executar o dashboard

Os dados já preparados estão em `data/`, então não é preciso baixar nada.

```bash
streamlit run app.py
```

Para encerrar o dashboard, pressione `Ctrl+C` no terminal.

## Regenerar os dados (opcional)

```bash
python prepare_data.py            # baixa da API (~20 s) e guarda cache em data/raw/
python prepare_data.py --refresh  # ignora o cache e baixa de novo
python check_data.py              # confere contra a Atividade 01
```

### Funil de preparação

| Etapa | Registros |
|---|---|
| Registros consolidados (2020–2025) | 326.623 |
| Sem duplicatas | 324.323 |
| Apartamentos em guias de unidade única | 119.493 |
| Valor e área privativa válidos | 119.492 |
| Sem ZN INDEFINIDA 2 | 118.655 |
| Sem bairro vazio | 118.568 |
| Sem atípicos (valor/m² entre P1 e P99) | 116.198 |

## Fontes dos dados

- ITBI, Prefeitura de Porto Alegre (Divisão da Receita Imobiliária). Portal de Dados Abertos: https://dadosabertos.poa.br/dataset/itbi. Licença Creative Commons Attribution. Acessado pela API `datastore_search`, com um `resource_id` por ano (ver `pipeline.py`).
- Limites de bairros, LC 12.112/2016 (SMURB/PMPA): https://dadosabertos.poa.br/dataset/a7172700-e0e2-4797-bf4a-12f658828568


## Explorador territorial

O mapa é o centro da aplicação. O público são famílias e compradores interessados em
compreender padrões históricos, além de corretores e avaliadores. A base não descreve
imóveis atualmente anunciados ou disponíveis.

### Perguntas e recursos

- **P1:** Como o valor mediano dos apartamentos evoluiu entre 2020 e 2025?
  Linhas Plotly: base de cálculo mediana (padrão) ou valor/m², referência da cidade e
  até quatro bairros. Tooltip com ano, região, mediana e quantidade.
- **P2:** Quais bairros têm os maiores e menores valores medianos?
  Barras Altair ordenáveis, padrão base de cálculo mediana, com mínimo de registros.
- **P3:** Como o valor por metro quadrado varia entre bairros?
  Mapa Folium agrupado por nome oficial, mantendo os 94 polígonos.
- Complementos: dispersão Plotly, painel do bairro em foco e tabela de até quatro bairros.
  Os números vêm do Parquet. Não há fotos de bairros nem dados ilustrativos.

### Filtros e cálculos

O panorama começa com todos os anos, bairros, valores e áreas, sem restrição de construção.
Contexto = período e bairros. Perfil = base de cálculo, área e construção.
Bairros sem seleção significa todos. Recorte sem registros gera aviso.
Limpar filtros restaura o panorama. Os limites das faixas vêm dos dados.

Há 23.154 registros sem ano de construção, mantidos por padrão; quando o filtro é ativado,
uma opção permite incluí-los ou excluí-los. O período usa o ano da base, sem assumir que
data_estimativa seja a data de venda.

Modos do mapa: valor/m², base de cálculo, quantidade, compatibilidade histórica e variação.
Compatibilidade = 100 × registros compatíveis / registros avaliados no bairro antes dos
filtros de perfil. O contexto conserva o período e os bairros escolhidos.
O mínimo (padrão 100) aplica-se ao denominador nesse modo. Zero observado difere de
ausência de contexto. Nas outras métricas, o mínimo se aplica à amostra filtrada.

Variação = 100 × (mediana final / mediana inicial − 1), nos anos extremos do intervalo.
Exige o mínimo em ambos os extremos; um único ano ou amostra insuficiente fica indisponível.
As séries não interpolam anos com poucos registros. Valores são nominais: não representam
retorno e podem refletir mudanças de composição.

Porto Alegre usa os mesmos filtros de período e perfil e todos os bairros, mesmo quando
a seleção territorial restringe as comparações locais. Medianas da cidade são calculadas
sobre registros, não pela média das medianas dos bairros. JAR ITU SABARA permanece nas
tabelas e séries, sem associação artificial a um polígono.

### Metodologia e limitações

Base de cálculo é uma medida fiscal, não preço de mercado confirmado. Valor/m² é a base
dividida pela área privativa. Transmissões parciais, corte P1–P99 e exclusão de guias
multiunidade são preservados. A mediana de construção considera apenas anos informados.
Contagens são registros selecionados, não imóveis únicos, estoque, liquidez ou tempo de venda.

### Código e validação

- metrics.py: filtros, agregações, compatibilidade, variação e formatação brasileira.
- app.py: estado, controles, tratamento de vazio e renderização.
- charts.py: construtores sem chamadas Streamlit.
- test_dashboard.py: cálculos e cenários de filtros com Streamlit AppTest.

Pipeline, geo.py, prepare_data.py, check_data.py e dados preparados são preservados.
O uso normal não consulta a API; o mapa-base OpenStreetMap depende de rede.
A seleção do bairro usa selectbox estável, com contorno azul no mapa.

Na pasta do aplicativo:

    python test_dashboard.py
    python check_data.py
    python -m streamlit run app.py

check_data.py consulta a API quando data/raw não está disponível.

### Windows: caminhos longos

Se ocorrer WinError 206, use um ambiente com caminho curto (PowerShell):

    python -m venv "$env:TEMP/itbi-venv"
    & "$env:TEMP/itbi-venv/Scripts/python.exe" -m pip install -r requirements.txt
    & "$env:TEMP/itbi-venv/Scripts/python.exe" -m streamlit run app.py
