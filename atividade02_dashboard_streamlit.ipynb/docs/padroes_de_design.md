# Padrão de design e visualizações do dashboard

Este documento orienta a identidade visual, a interação e a implementação das visualizações do dashboard de ITBI de Porto Alegre. O público principal são compradores e famílias em busca do primeiro imóvel; corretores e avaliadores são públicos secundários. A interface deve facilitar comparação e leitura de dados, sem parecer uma página promocional.

## Identidade visual

A bandeira de Porto Alegre é branca, com o brasão municipal ao centro, conforme a Lei Municipal nº 3.893/1974. O dashboard deve seguir essa identidade:

- Use branco como cor predominante de fundo, refletindo a bandeira e preservando espaço visual para os dados.
- Derive as cores de destaque dos tons presentes no brasão oficial. Não invente uma paleta municipal nem fixe valores hexadecimais sem conferir o arquivo oficial do brasão.
- O SVG oficial do brasão define azul `#3669B2`, vermelho `#E40A24`, verde `#4AB05B` e ouro `#FFD402`; a bandeira usa campo branco `#FFFFFF`. Use esses códigos em cores de acento quando houver contraste suficiente. Para linhas e textos pequenos, use os tons escurecidos `#1B5E45` (verde) e `#805D0F` (ouro), já adotados no tema.
- Use cinzas neutros para textos secundários, divisórias e estados desabilitados. Reserve as cores do brasão para hierarquia, seleção e destaque de dados.
- Mantenha as cores semânticas consistentes entre gráficos. Uma mesma categoria ou estado deve conservar sua cor em todo o dashboard.
- Em escalas quantitativas, use uma sequência ordenada, legível e coerente com a identidade municipal. Não use arco-íris nem dependa apenas da cor para comunicar o valor.
- Garanta contraste suficiente entre texto, fundo, linhas e áreas preenchidas; combine cores com rótulos, unidades, legenda ou tooltip.

Referência municipal: [Bandeira de Porto Alegre — Informações da Cidade (PMPA, arquivo histórico)](https://web.archive.org/web/20070611023133/http://www2.portoalegre.rs.gov.br/infocidade/default.php?reg=3&p_secao=22).
O brasão municipal associa ouro, azul, verde, vermelho e prata às cores e símbolos locais: [Brasão de Porto Alegre — Informações da Cidade (PMPA, arquivo histórico)](https://web.archive.org/web/20070611023125/http://www2.portoalegre.rs.gov.br/infocidade/default.php?reg=2&p_secao=22).

## Hierarquia e composição

- Apresente um título direto, seguido de contexto curto sobre o recorte, a fonte e a interpretação das medidas.
- Organize a página na ordem de uso: filtros, indicadores de resumo e, em seguida, visualizações detalhadas.
- Use títulos de seção e espaçamento para agrupar conteúdo relacionado. Evite painéis decorativos, excesso de cartões e elementos que disputem atenção com os dados.
- Dê prioridade ao mapa e aos gráficos na área principal; deixe controles globais na barra lateral.
- Use `st.container` ou colunas apenas quando ajudarem a agrupar ou comparar conteúdo. Preserve a leitura em telas estreitas.

## Tipografia, rótulos e números

- Use tipografia simples e legível, com hierarquia consistente entre título da página, seções, títulos de gráficos e texto de apoio.
- Escreva em português e prefira frases curtas, termos compreensíveis e capitalização de frase.
- Explique “mediana” e “base de cálculo” em linguagem simples. Deixe claro que a base de cálculo é uma base fiscal do ITBI, usada como aproximação, e não necessariamente o preço de mercado.
- Identifique unidades em eixos, legendas e tooltips: R$, R$/m², m² ou ano, conforme a variável.
- Formate valores monetários de modo consistente e localizável para o público brasileiro; mantenha a mesma precisão dentro de cada visualização.
- Evite nomes internos de colunas, abreviações sem explicação e texto cortado.

## Interação e estados

- Use controles adequados à escolha: slider para intervalos numéricos, multiselect para bairros e controle de seleção para métricas.
- A seleção padrão deve mostrar o panorama completo disponível. Cada filtro deve atualizar todas as visualizações a que se aplica, sem deixar gráficos com períodos ou populações diferentes por acidente.
- Identifique o período, as métricas e a população usados na tela. Quando os filtros não retornarem dados, mostre um aviso claro e não desenhe gráficos vazios.
- Mantenha filtros e títulos estáveis durante reruns; atribua chaves explícitas quando controles puderem se repetir.

## Gráficos e mapas

Escolha a forma visual de acordo com a pergunta: linhas para evolução temporal, barras ordenadas para rankings e coroplético para padrões geográficos. Cada visualização deve ter título, unidade, legenda ou tooltip e uma frase curta de leitura quando isso ajudar na interpretação.
- Preserve a escala `YlOrRd` já definida para o coroplético do mapa: ela codifica o valor e deve permanecer estável, separada das cores do tema geral.

Para o mapa por bairro:

- Mantenha todos os polígonos oficiais do GeoJSON, mesmo quando não houver transações no período selecionado.
- Use a mediana do valor por m² por `bairro_oficial`; mantenha uma escala ordenada, legenda em R$/m² e tooltip com bairro e valor.
- Mostre áreas sem dados com uma cor neutra distinta da escala. Não as confunda com valores baixos ou zero.
- Enquadre o mapa nos limites municipais, destaque o contorno externo de Porto Alegre e não exiba mapa-base de cidades vizinhas.
- Categorias sem geometria, como `JAR ITU SABARA`, não podem ser desenhadas. Informe-as separadamente; não atribua seus registros a outro bairro.

## Responsabilidades no código

- `app.py` configura a página, carrega os dados, apresenta controles, aplica filtros, trata estados vazios, organiza a hierarquia e renderiza as visualizações.
- `charts.py` contém um construtor independente por visualização. Cada construtor recebe os dados já filtrados e parâmetros adicionais explícitos, calcula apenas a agregação específica do gráfico e retorna o objeto visual.
- `pipeline.py` é responsável pela preparação compartilhada dos dados. Não duplique o funil em `app.py` ou `charts.py`.

Os construtores não chamam APIs `st.*`, não carregam arquivos e não alteram o DataFrame recebido. A renderização fica em `app.py`:

| Objeto retornado | Renderização em `app.py` |
|---|---|
| Figura Plotly | `st.plotly_chart(...)` |
| Gráfico Altair | `st.altair_chart(...)` |
| Mapa Folium | `st_folium(...)` |

Use nomes descritivos no formato `build_<visualizacao>`. Mantenha os construtores juntos em `charts.py` enquanto o módulo continuar simples; crie outro módulo apenas quando houver uma necessidade concreta de separar uma família ou lógica realmente compartilhada.

Exemplo do fluxo atual:

```python
# charts.py
def build_yearly_median_chart(df_filtrado):
    dados_do_grafico = ...
    grafico = ...
    return grafico

# app.py
st.subheader("Título da visualização")
st.plotly_chart(build_yearly_median_chart(df_filtrado), width="stretch")
```

## Acessibilidade e validação

- Não comunique diferenças apenas por cor; complemente-as com rótulos, padrões, símbolos ou tooltips.
- Use contraste legível, controles acessíveis por teclado e nomes claros para os widgets.
- Faça títulos, rótulos e valores caberem em desktop e celular; prefira quebra de linha a corte ou sobreposição.
- Valide cálculos com `check_data.py` quando houver valores de referência. Use `AppTest` ou execute o app para confirmar que a visualização renderiza sem exceções.
- Revise combinações de filtros, seleção vazia, dados ausentes e categorias sem geometria antes de considerar um gráfico concluído.