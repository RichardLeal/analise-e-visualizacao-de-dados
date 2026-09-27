# Escopo do dashboard — Atividade 02

> **Proposta para o grupo validar.** Os itens marcados com ❓ precisam de decisão antes do desenvolvimento do app (T06–T12).

## Público
**Principal:** comprador / família em busca do 1º imóvel. Foi a motivação do grupo na Atividade 01 (seção 2) e é o perfil que o próprio grupo e seus conhecidos conseguem avaliar (seção 7).

**Secundários** (o mesmo dashboard atende): corretor e avaliador de imóveis, que comparam valor/m² entre bairros e anos.

Consequência para a interface: linguagem simples, explicar "mediana" e "base de cálculo" em uma frase, valores sempre em R$ e R$/m².

## Perguntas da Atividade 01 contempladas
As três perguntas da Atividade 01 (o mínimo exigido é duas):

| Nº | Pergunta | Onde aparece no dashboard |
|---|---|---|
| P1 | Como o valor mediano dos apartamentos evoluiu entre 2020 e 2025? | Gráfico 1 (linha) |
| P2 | Quais bairros têm os maiores e menores valores medianos? | Gráfico 2 (barras), métrica "valor total" |
| P3 | Como o valor por m² varia entre bairros? (prioritária) | Gráfico 2, métrica "valor/m²", e Gráfico 3 (mapa) |

## Visualizações e bibliotecas
São exigidas pelo menos 3 visualizações, feitas com pelo menos 2 bibliotecas. A proposta usa 3 bibliotecas:

| # | Gráfico | Biblioteca | Pergunta | Por quê |
|---|---|---|---|---|
| 1 | Linha: mediana por ano, da cidade e dos bairros selecionados | **Plotly** | P1 | Tooltip com o valor exato por ano; comparar bairros com a cidade |
| 2 | Barras horizontais ordenadas: mediana por bairro | **Altair** | P2, P3 | Ranking legível com nomes longos; tooltip com o número de registros |
| 3 | Mapa coroplético: valor/m² mediano por bairro | **Folium** | P3 | Padrão territorial, que tabela e barras não mostram |
| 4 (opcional) | Distribuição (boxplot ou histograma) do valor/m² nos bairros selecionados | Altair ou Plotly | P3 | Mostra a dispersão, não só a mediana |

Os gráficos 1 e 2 seguem o filtro de métrica (valor total ou valor/m²). O mapa usa sempre valor/m², porque comparar valor total entre bairros confunde preço com tamanho do imóvel.

### Organização dos gráficos no código

Cada visualização deve ter um construtor próprio em `charts.py`, que recebe os dados já filtrados e retorna o objeto da biblioteca correspondente. `app.py` organiza a página, aplica os filtros, trata seleções sem dados e renderiza cada objeto. Consulte [`docs/padroes_de-design.md`](padroes_de-design.md) para o padrão visual e a lista de responsabilidades.

## Controles interativos
São exigidos pelo menos 2:

| Controle | Tipo | Afeta |
|---|---|---|
| Período (ano inicial–final) | `st.slider` (faixa) | todos |
| Bairros | `st.multiselect` | gráfico 1 (linhas por bairro) e destaque no gráfico 2 |
| Métrica: valor total (R$) ou valor/m² (R$/m²) | `st.radio` | gráficos 1 e 2, KPIs |
| Mínimo de registros por bairro | `st.slider` (padrão 100, como na Atividade 01) | gráficos 2 e 3 |
| ❓ Faixa de área privativa (m²) | `st.slider` | todos. Útil para o comprador ("apês de 40 a 70 m²") |

Seleção vazia: usar `st.warning("Nenhum apartamento para os filtros escolhidos…")` e não desenhar o gráfico.

## Dados
- **Arquivo:** `data/apartamentos_itbi_poa.parquet`, com 116.198 apartamentos, gerado por `prepare_data.py` com o mesmo funil da Atividade 01.
- **Mapa:** `data/bairros_poa.geojson`, com os limites oficiais da LC 12.112/2016, 94 bairros.
- **Conferência:** `check_data.py` reproduz os números da Atividade 01 (funil, medianas por ano e por bairro). Todos batem.
- **Fonte a citar no app:** Prefeitura de Porto Alegre, Portal de Dados Abertos, conjunto ITBI (https://dadosabertos.poa.br/dataset/itbi), licença CC-BY. Limites de bairros: SMURB/PMPA, LC 12.112/2016.

### Mudanças em relação à Atividade 01
Estas mudanças devem ser citadas no "Registro do grupo".
1. **84 registros com bairro vazio excluídos.** Na Atividade 01 eles passaram pelo funil e apareciam como um bairro "em branco". Base final: 116.198 registros, contra 116.282 na Atividade 01. Os limites do corte P1–P99 praticamente não mudam: R$ 1.041,67 a R$ 16.301,07 por m².
2. **Agrupamento pelo nome oficial do bairro** (coluna `bairro_oficial`), e não pelo nome truncado do ITBI. Exemplos: "CENTRO HISTORIC" vira "CENTRO HISTÓRICO"; "PASSO DAS PEDRA" e "PASSO PEDRAS" viram "PASSO DAS PEDRAS", que antes contavam como dois bairros.
3. **Mapa com 84 de 85 bairros.** Na Atividade 01 eram 13 sem correspondência. A tabela completa está em `data/bairros_correspondencia.csv`.

### ❓ Decisões pendentes
- **Percentual transmitido < 100%:** 3.646 registros (3,1%) transmitem só parte do imóvel. Se `base_de_calculo` se refere à fração, o valor/m² desses registros sai subestimado. A Atividade 01 manteve esses registros. Opções: manter e citar como limitação, ou excluir. É preciso checar no dicionário de dados.
- **"JAR ITU SABARA" (134 registros):** é o antigo bairro Jardim Itu-Sabará, dividido em Jardim Itu e Jardim Sabará pela LC 12.112/2016. Não tem polígono único. Hoje fica nos gráficos 1 e 2 e fica fora do mapa. Alternativa: excluir.
- **Nome exibido:** oficial com acento ("CENTRO HISTÓRICO", proposta) ou o do ITBI.

## Limitações a citar no app e no registro
- `base_de_calculo` é a base fiscal do ITBI, usada como proxy de preço; não é o preço de mercado.
- O corte P1–P99 remove cerca de 2% dos registros e pode descartar extremos legítimos.
- O ano é o ano do arquivo do ITBI. As datas de estimativa de cada ano ficam dentro do próprio ano, e 2025 está completo (de 02/01 a 31/12).
