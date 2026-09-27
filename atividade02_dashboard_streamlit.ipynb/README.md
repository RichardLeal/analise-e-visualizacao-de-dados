# Apartamentos em Porto Alegre — Dashboard ITBI (2020–2025)

IA001 — Análise e Visualização de Dados (Especialização em IA Avançada, INF-UFRGS). Atividade 02: dashboard interativo em Streamlit.

Grupo: Giulia Giozza, Richard Ramos, Eduardo Mello.

## Estrutura

Todos os comandos abaixo são executados dentro desta pasta (`atividade02_dashboard_streamlit.ipynb/`).

| Arquivo | O que é |
|---|---|
| `app.py` | Aplicação Streamlit |
| `charts.py` | Construtores dos gráficos; um por visualização |
| `pipeline.py` | Carga da API e funil de preparação (mesmas regras da Atividade 01) |
| `geo.py` | Limites oficiais dos bairros e casamento com os nomes do ITBI |
| `prepare_data.py` | Gera os arquivos em `data/` |
| `check_data.py` | Confere os dados contra os números entregues na Atividade 01 |
| `data/apartamentos_itbi_poa.parquet` | Base analítica (um apartamento por linha) |
| `data/bairros_poa.geojson` | Limites dos bairros (WGS84) |
| `data/bairros_correspondencia.csv` | Nome no ITBI → nome oficial |
| `data/funil.csv` | Registros restantes após cada etapa |
| `docs/escopo.md` | Público, perguntas, gráficos e filtros do dashboard |
| `docs/padroes_graficos.md` | Padrão para implementar e integrar novos gráficos |
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
