# 5. Guia de estudo

> Um roteiro para dominar o projeto e os assuntos por trás dele, com perguntas para treinar a
> apresentação e sugestões de conteúdo para estudar por fora. As referências marcadas com 🆓 são
> gratuitas online.

## 5.1 Roteiro sugerido (por tema)

| Etapa | Estude | Use o projeto para praticar |
|---|---|---|
| 1. A história | Leia o site inteiro e depois [02-dados.md](02-dados.md) §2.3 (decisões) | Explique em 2 minutos a reviravolta do cap. 3 |
| 2. Tipos de dados e codificação | [03-tipos-de-dados.md](03-tipos-de-dados.md); Munzner cap. 2 e 5 | Classifique todas as variáveis da tabela do Explore |
| 3. Cor | Wilke cap. 4 e 19; ColorBrewer | Por que a escala do mapa concentra tons no topo? |
| 4. Estatística | [04-metodos.md](04-metodos.md); OpenIntro caps. 1–2 e 8 | Recalcule um ρ de Spearman à mão com 5 municípios |
| 5. Espaço | Moran (1950), Anselin (1995); *Geocomputation with Python* | Interprete os três I de Moran do cap. 4 |
| 6. D3 | Documentação do D3; Murray ou Wattenberger | Mude a cor de uma série e o tamanho de um ponto |
| 7. Scrollytelling | Bostock "How to Scroll"; The Pudding | Acrescente um passo ao cap. 1 |
| 8. Acessibilidade | WCAG 2.2 (contraste, teclado); `prefers-reduced-motion` | Navegue o Explore só com o teclado |
| 9. Ética e limites | Robinson (1950); Cairo, *How Charts Lie* | Explique a falácia ecológica com o voto |

## 5.2 Perguntas para treinar a apresentação

**Sobre a história**
1. Qual é a pergunta do projeto, numa frase?
2. Quais eram os "suspeitos" e por que cada um foi descartado?
3. O que é a "reviravolta" e quais três correções de medida ela envolve?
4. Quem ficou para trás, afinal? Por que "começaram atrás **e** não voltaram"?
5. Qual é o único sinal político que sobra, e por que não podemos dizer que ele é causa?

**Sobre os dados**
6. Por que o Censo 2022 e não a estimativa de 2021?
7. Por que contar pessoas e não doses? Dê um número que mostra a diferença.
8. Por que residência e não local de aplicação?
9. O que é o abandono individual e por que o agregado podia dar negativo?
10. Por que Itaitinga não é chamada de "pior do estado"?

**Sobre a visualização**
11. Por que um mapa no cap. 3 e uma dispersão no cap. 2?
12. O que a faixa P10–P90 mostra que a média esconde?
13. Por que a cor do mapa tem teto em 100%, e como o site mostra os valores acima?
14. Para que servem as coordenadas paralelas no Explore?
15. Como um leitor que não enxerga as cores identifica os perfis do cap. 4?

**Perguntas difíceis (que a banca pode fazer)**
16. "Correlação de −0,19 é fraca. Por que dar destaque?" → Não damos: mostramos que ela some com controles.
17. "Com R² de 23%, o projeto não explicou nada?" → Explicou o que *não* é a causa e corrigiu a medida;
    o resto aponta para fatores locais não medidos.
18. "Os 13 foram escolhidos com doses e o site conta pessoas. Não é inconsistente?" → É o critério das
    verificações, declarado no texto; com pessoas são 39 abaixo de 70%, e os 13 estão entre os 16 menores.
19. "Por que não usar o município de aplicação?" → Fortaleza teria 219%: o campo registra muitas doses
    do interior em estabelecimentos cadastrados na capital.

## 5.3 Sugestões de conteúdo

### Visualização de dados — fundamentos

- **Tamara Munzner — *Visualization Analysis and Design*** (CRC Press, 2014). A referência para
  tipos de dados, tarefas e codificação (o "what, why, how"). Base do [03-tipos-de-dados.md](03-tipos-de-dados.md).
- **Claus O. Wilke — *Fundamentals of Data Visualization*** (O'Reilly, 2019). 🆓 em
  [clauswilke.com/dataviz](https://clauswilke.com/dataviz). Muito prático: cores, eixos, proporções, erros comuns.
- **Alberto Cairo — *The Functional Art*** (2012) e ***How Charts Lie*** (2019). Jornalismo de dados e
  como gráficos enganam (inclusive mapas).
- **Edward Tufte — *The Visual Display of Quantitative Information*** (2ª ed., 2001). Clássico sobre
  densidade de dados e "tinta" desnecessária.
- **Cleveland, W. S. e McGill, R. (1984)** — "Graphical Perception", *Journal of the American
  Statistical Association*. O estudo que ordenou os canais visuais por precisão.

### Mapas

- **Mark Monmonier — *How to Lie with Maps*** (3ª ed., 2018). Por que coropléticos enganam e como evitar.
- **Kenneth Field — *Cartography.*** (Esri Press, 2018). Cartografia temática, classificação, cor.
- **Dorman, Graser, Nowosad e Lovelace — *Geocomputation with Python*** 🆓 em
  [py.geocompx.org](https://py.geocompx.org). Dados espaciais em Python (GeoPandas, vizinhança, mapas).

### Cor e acessibilidade

- **ColorBrewer** 🆓 — [colorbrewer2.org](https://colorbrewer2.org) (Cynthia Brewer). Paletas sequenciais,
  divergentes e qualitativas testadas para mapas.
- **WCAG 2.2** 🆓 — [w3.org/TR/WCAG22](https://www.w3.org/TR/WCAG22/). Contraste, teclado, alternativas textuais.
- **Coblis** (simulador de daltonismo) 🆓 — útil para testar uma imagem rapidamente.

### D3 e desenvolvimento web

- **Documentação oficial do D3** 🆓 — [d3js.org](https://d3js.org). Leia *Getting started*, escalas,
  eixos, seleções/joins e transições.
- **Observable** 🆓 — [observablehq.com](https://observablehq.com). Exemplos de D3 editáveis no navegador.
- **Scott Murray — *Interactive Data Visualization for the Web*** (2ª ed., 2017). Introdução didática ao
  D3 (versão 4; os conceitos valem para a 7).
- **Amelia Wattenberger — *Fullstack D3 and Data Visualization*** (Fullstack.io). Do zero a gráficos
  interativos completos.
- **MDN Web Docs** 🆓 — [developer.mozilla.org](https://developer.mozilla.org). Referência de HTML, CSS
  (`position: sticky`, Grid) e JavaScript (módulos, `IntersectionObserver`, `ResizeObserver`).

### Scrollytelling

- **Mike Bostock — "How To Scroll"** (2014) 🆓 — [bost.ocks.org/mike/scroll](https://bost.ocks.org/mike/scroll/).
  Quando a rolagem ajuda e quando atrapalha.
- **Scrollama** 🆓 — [github.com/russellsamora/scrollama](https://github.com/russellsamora/scrollama).
  Leia o README e os exemplos (*sticky graphic*, *progress*).
- **The Pudding** 🆓 — [pudding.cool](https://pudding.cool). Ensaios visuais para estudar estrutura
  narrativa; a seção de bastidores explica como alguns foram feitos.
- Para referência de tom: **NYT The Upshot** e **Folha Gráficos**.

### Estatística

- **Diez, Çetinkaya-Rundel e Barr — *OpenIntro Statistics*** 🆓 em
  [openintro.org](https://www.openintro.org/book/os/). Correlação, testes, regressão, com linguagem simples.
- **Bussab e Morettin — *Estatística Básica*** (Saraiva). Clássico brasileiro, bom para as fórmulas.
- **Benjamini, Y. e Hochberg, Y. (1995)** — "Controlling the False Discovery Rate", *Journal of the
  Royal Statistical Society, Series B*. O artigo do FDR (curto e legível nas primeiras páginas).
- **Moran, P. A. P. (1950)** — "Notes on Continuous Stochastic Phenomena", *Biometrika*. Origem do I de Moran.
- **Anselin, L. (1995)** — "Local Indicators of Spatial Association — LISA", *Geographical Analysis*.
- **Robinson, W. S. (1950)** — "Ecological Correlations and the Behavior of Individuals",
  *American Sociological Review*. O texto que nomeou a falácia ecológica.

### Python para dados

- **Wes McKinney — *Python for Data Analysis*** (3ª ed., 2022) 🆓 em
  [wesmckinney.com/book](https://wesmckinney.com/book/). Do criador do pandas.
- **Documentação do pandas** 🆓 — leia *10 minutes to pandas*, *Group by* e *Reshaping* (pivot).

### Dados públicos brasileiros

- **Portal de Dados Abertos do SUS** 🆓 — `dadosabertos.saude.gov.br` (vacinação, com dicionário de dados).
- **IBGE SIDRA** 🆓 — [sidra.ibge.gov.br](https://sidra.ibge.gov.br) e a API de agregados
  (`servicodados.ibge.gov.br/api/docs/agregados`).
- **TSE Dados Abertos** 🆓 — [dadosabertos.tse.jus.br](https://dadosabertos.tse.jus.br) (resultados,
  candidatos, correspondência de códigos).
- **DATASUS / TabNet e FTP** 🆓 — CNES, SI-PNI e outros sistemas do SUS.
- **Base dos Dados** 🆓 — [basedosdados.org](https://basedosdados.org). Muitas dessas bases já limpas
  e padronizadas.
- **W. Cota — covid19br** 🆓 — [github.com/wcota/covid19br](https://github.com/wcota/covid19br),
  séries de casos e óbitos por município.

## 5.4 Exercícios práticos com o próprio projeto

1. **Trocar o denominador:** no `preparar_site.py`, mude o estado (c) do cap. 3 para usar `pop2021`.
   Quantos municípios ficam acima de 100%? (Resposta nas verificações: 20.)
2. **Novo suspeito:** acrescente "população rural (%)" como 6º passo do cap. 2 (dados já estão em
   `base_analise.csv`; siga o padrão de `cap2()` no preparo e de um `.passo` no HTML).
3. **Ler um gráfico sem cor:** abra o site, ative a simulação de daltonismo do Chrome
   (DevTools → Rendering → *Emulate vision deficiencies*) e verifique se os perfis do cap. 4 continuam
   distinguíveis.
4. **Testar a robustez da decomposição:** mude o corte de 65% para 60% em `verificacoes_finais.py`.
   Quantos perfis mudam?
5. **Moran à mão:** escolha um município e seus vizinhos no Explore; calcule a média dos vizinhos e
   compare com o valor do município. Repita para três municípios e veja se "parecem com os vizinhos".

## 5.5 Glossário rápido

| Termo | Significado |
|---|---|
| Cobertura | Pessoas vacinadas ÷ população |
| Esquema completo | 2ª dose ou dose única |
| Abandono individual | Pessoas com 1ª dose e sem 2ª ÷ pessoas com 1ª dose |
| Denominador | O "÷ população" da cobertura; escolher qual população muda o resultado |
| P10, P90 | Percentis: 10% e 90% dos municípios ficam abaixo desses valores |
| ρ (rô) | Correlação de postos de Spearman |
| ρ parcial | Correlação depois de descontar variáveis de controle |
| q (FDR) | Valor-p ajustado para muitos testes |
| R² | Fração da variação explicada por um modelo |
| I de Moran | Mede se vizinhos se parecem (manchas no mapa) |
| Falácia ecológica | Concluir sobre pessoas a partir de dados agregados |
| Coroplético | Mapa em que cada região é pintada pelo seu valor |
| Scrollytelling | Narrativa em que a rolagem conduz os gráficos |
| Data join | Mecanismo do D3 que liga cada dado a um elemento visual |
| Visões coordenadas | Vários gráficos que reagem juntos à mesma seleção |
