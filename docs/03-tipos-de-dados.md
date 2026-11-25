# 3. Tipos de dados, codificação visual e formatos

> Por que um mapa e não barras? Por que azul claro→escuro e não arco-íris? A resposta começa no **tipo**
> de cada dado. Este documento usa a classificação de Tamara Munzner (*Visualization Analysis and
> Design*) e a de Stevens, aplicadas variável por variável do projeto.

## 3.1 Tipos de conjunto de dados (*dataset types*)

| Tipo | O que é | No projeto |
|---|---|---|
| **Tabela** | Linhas (itens) × colunas (atributos) | Uma linha por município, ~60 atributos (`base_analise.csv`) |
| **Rede** | Itens ligados por relações | Vizinhança entre municípios (quem faz fronteira com quem), usada no I de Moran |
| **Geometria (espacial)** | Formas com posição no espaço | Polígonos dos 184 municípios (`geo.json`) |
| **Série temporal** | Valores ordenados no tempo | Cobertura acumulada semanal; doses por dia |

Um mesmo item (o município) aparece nos quatro tipos. É isso que permite as **visões coordenadas** do
capítulo 7: o município é a "cola" entre mapa, dispersão, paralelas e tabela.

## 3.2 Tipos de atributo

### Escalas de medida (Stevens, 1946)

| Escala | Operações válidas | Exemplo no projeto |
|---|---|---|
| **Nominal** (categórico) | = ≠ | Partido do prefeito; nome do município; vacina |
| **Ordinal** | = ≠ < > | Posição no ranking (184º de 184); classes de quantil do mapa. Atenção: os perfis dos 13 parecem ordenados, mas são **nominais** (nenhum é "maior" que outro) |
| **Intervalar** | + − (diferenças) | Data (diferença entre datas faz sentido, razão não) |
| **De razão** | + − × ÷ (zero verdadeiro) | Doses, pessoas, população, renda, cobertura, distância |

Pergunta-teste: "o dobro" faz sentido? Renda R$ 1.000 é o dobro de R$ 500 (razão). 2 de janeiro não
é "o dobro" de 1º de janeiro (intervalar).

### Na linguagem de Munzner

- **Categórico:** sem ordem. Codificar com **matiz** (cor diferente) ou forma.
- **Ordenado — sequencial:** de pouco a muito (cobertura, renda). Codificar com **posição**, **comprimento**
  ou **luminosidade** de um só matiz.
- **Ordenado — divergente:** com ponto central significativo (variação do voto: negativa / zero / positiva).
  Dois matizes + neutro no meio.
- **Ordenado — cíclico:** dia da semana, mês. No calendário, a semana vira linha.

## 3.3 Cada variável do projeto

| Variável | Tipo | Unidade | Faixa | Codificação usada | Onde |
|---|---|---|---|---|---|
| Esquema completo (pessoas ÷ Censo) | Quantitativa, razão, sequencial | % | 40%–112% | Posição (eixo Y), cor sequencial no mapa | Caps. 2, 4, 7 |
| 1ª dose (3 estados) | Quantitativa, razão | % | 50%–168% | Cor sequencial + contorno de alerta > 100% | Cap. 3 |
| Abandono individual | Quantitativa, razão | % | 5%–42% | Comprimento da linha no funil; eixo | Caps. 4, 7 |
| Reforço | Quantitativa, razão | **doses por habitante** (não %) | 0,3–1,9 | Posição no enxame | Cap. 5 |
| Data / semana | Temporal, intervalar | dia | 2021–2024 | Eixo X; grade dia × semana | Cap. 1 |
| Doses por dia | Quantitativa, contagem | doses | 3–128 mil | Cor sequencial em 6 faixas | Cap. 1 |
| Renda mediana | Quantitativa, razão | R$ | 303–1.212 | Eixo X | Caps. 2, 4, 7 |
| Voto em Bolsonaro 2018 | Quantitativa, razão (proporção) | % dos válidos | 9%–44% | Eixo X; mapa por quantil | Caps. 2, 4 |
| Variação do voto 2018→2022 | Quantitativa, **divergente** | pontos percentuais | −4 a +12 | Eixo X (zero visível) | Cap. 5 |
| Equipes por 10 mil hab. | Quantitativa, taxa | equipes/10 mil | 1,9–6,8 | Eixo X | Caps. 2, 7 |
| Perfil dos 13 | **Categórica nominal** | — | 3 classes | Matiz **e** forma | Cap. 4 |
| Acima de 100% | Categórica (sim/não), derivada | — | — | Contorno terracota + ▲ | Caps. 2, 3, 7 |
| Sensível ao denominador | Categórica, derivada | — | — | Textura (hachura) | Cap. 3 |
| Município | Categórica nominal (identificador) | — | 184 | Posição no mapa; rótulo | todos |
| I de Moran | Quantitativa (estatística) | adimensional | −1 a 1 | Número no painel | Cap. 4 |

### Dados derivados (não vieram prontos)

Muito do que o site mostra é **derivado**: calculado a partir de outros dados. Saber distinguir é
essencial para explicar o projeto.

- **Taxas e proporções:** cobertura = pessoas ÷ população. O denominador muda o resultado (cap. 3 inteiro).
- **Contagem de distintos:** pessoas a partir de registros (remove duplicidade).
- **Percentis:** P10 e P90 da cobertura em cada semana (faixa do cap. 1).
- **Postos (ranks):** "184º de 184"; base das correlações de Spearman.
- **Classes de quantil:** mapas do I de Moran (cada cor ≈ 1/7 dos municípios).
- **Categorias derivadas:** "acima de 100%", perfis dos 13 (a partir da decomposição).

## 3.4 Do tipo para a forma do gráfico

| Pergunta | Tipo dos dados | Forma escolhida | Por quê |
|---|---|---|---|
| Como a cobertura evoluiu? | Temporal + quantitativa | Linha | Posição no eixo comum é o canal mais preciso; linha mostra continuidade |
| Quanto variava entre municípios? | Distribuição por semana | Faixa (área P10–P90) | Mostra a dispersão sem 184 linhas sobrepostas |
| Em que dias se vacinou mais? | Temporal cíclico + quantitativa | Calendário (heatmap) | Semana × dia revela padrões (fim de semana, mutirões) |
| Uma hipótese explica a cobertura? | Duas quantitativas | Dispersão | Relação entre dois atributos; cada ponto é um município |
| Onde estão? | Espacial + quantitativa | Mapa coroplético | Pergunta é geográfica |
| Formam manchas? | Espacial, comparar 3 variáveis | Pequenos múltiplos (3 mapas) | Mesma forma, variáveis diferentes, lado a lado |
| Onde se perde gente? | 2 quantitativas por item + categoria | Funil (*dumbbell*) | A distância entre os dois pontos *é* o abandono |
| Como se distribui o reforço? | 1 quantitativa, 184 itens | Enxame (*beeswarm*) | Mostra cada município sem empilhar |
| Comparar 7 medidas ao mesmo tempo | Multivariada | Coordenadas paralelas | Um eixo por variável; padrões aparecem como feixes de linhas |

**Cuidado com mapas coropléticos:** a área do município domina a percepção. Municípios grandes e pouco
populosos parecem mais importantes do que são. Por isso o mapa nunca está sozinho: há dispersão,
tabela e números.

## 3.5 Canais visuais e precisão

Cleveland e McGill (1984) mediram a precisão com que lemos cada canal. Do mais ao menos preciso:

1. Posição num eixo comum (dispersão, linha)
2. Posição em eixos não alinhados (pequenos múltiplos)
3. Comprimento (funil)
4. Ângulo, inclinação
5. Área
6. Luminosidade, saturação (mapa coroplético)
7. Matiz (só para categorias)

Consequência no projeto: comparações finas usam **posição** (dispersão, funil); a cor do mapa serve
para ver o padrão geral, e o número exato fica no detalhe e na tabela.

## 3.6 Cor

Cada cor faz **um** trabalho:

| Trabalho | Regra | Paleta no site |
|---|---|---|
| **Sequencial** (quanto) | Um matiz, do claro ao escuro | Cobertura: 7 tons de azul `#86AFC4 → #11344E`; doses: 6 tons de terracota |
| **Categórico** (qual) | Matizes distintos, ordem fixa | Perfis: azul `#2A5FA0`, terracota `#C0633A`, amarelo `#DDA73B` |
| **Divergente** (de que lado) | Dois matizes + cinza neutro | Não usado em mapa (a variação do voto aparece em eixo) |
| **Alerta** | Cor reservada + símbolo | Terracota em contorno + ▲ para "acima de 100%" |

Cores de **interface** (areia, tinta, terracota, sol, mar, carnaúba) são separadas das cores de **dados**.

Todas as paletas de dados foram **validadas por script**, não no olho:
- Luminosidade crescente e passos visíveis (ΔL ≥ 0,06) nas sequenciais.
- Separação para daltonismo (protanopia e deuteranopia simuladas) nas categóricas.
- Contraste mínimo de 2:1 da ponta clara contra o fundo.
- Os três perfis com luminância 0,11 / 0,20 / 0,43, que se distinguem também em cinza (impressão).

**Teto de 100% só na cor:** valores acima de 100% usam a cor do topo, mas aparecem com o valor real no
detalhe e com contorno de alerta. Cortar o valor em 100% esconderia o problema de medida.

**Escala não linear no mapa:** a maioria dos municípios fica entre 85% e 100%. Com passos iguais de 50%
a 100%, tudo sairia azul-escuro. Os tons foram concentrados no topo (60, 70, 80, 85, 90, 95, 100%) —
e a legenda mostra blocos, não um gradiente contínuo, para não esconder essa escolha.

## 3.7 Formatos de arquivo encontrados

| Formato | Onde | O que saber |
|---|---|---|
| **CSV** | quase tudo | Separador pode ser `;` (TSE, SIDRA, OpenDataSUS) ou `,`. Codificação: **latin-1** no TSE, **UTF-8 com BOM** no SIDRA. Decimal com vírgula e milhar com ponto nas fontes brasileiras |
| **CSV.GZ** | `dados/brutos/vacinacao/`, `dados/brutos/tse/` | CSV comprimido; o pandas lê direto pela extensão |
| **ZIP** | TSE, Downloads | Vários CSVs dentro (um por UF); ler só o necessário |
| **JSON** | `json/` (site) | Objetos e listas; o navegador lê nativamente |
| **GeoJSON** | malha | JSON com `type: Feature`, `geometry` (coordenadas lon/lat) e `properties`. O D3 exige anéis externos no sentido horário |
| **DBC / DBF** | CNES | DBF é o formato do dBase (tabela binária com cabeçalho de colunas). DBC é DBF comprimido (PKWare *implode*), formato do DATASUS |
| **XLSX** | e-Gestor | Planilha; não usada no fim |

### Valores especiais (armadilhas)

| Valor | Fonte | Significa |
|---|---|---|
| `-` | SIDRA | Zero absoluto |
| `...` | SIDRA | Não disponível |
| `#NULO#`, `-1` | TSE | Sem informação |
| `900001` | CNES (`DT_DESAT`) | Equipe nunca desativada |
| `None` | OpenDataSUS (CEP) | Vazio |
| Linhas sem data | covid19br-vac | 2.528 linhas; contam no total, não na série |

## Perguntas de revisão

1. Classifique: partido do prefeito, data da dose, renda mediana, posição no ranking.
2. Por que a variação do voto é "divergente" e a cobertura é "sequencial"?
3. Por que os perfis do capítulo 4 têm forma além de cor?
4. Por que um arco-íris seria uma má escolha para a cobertura?
5. Qual canal visual é mais preciso, e onde o projeto o usa para as comparações importantes?
6. Por que o mapa do I de Moran usa quantis e o mapa do capítulo 3 usa uma escala contínua?
7. Dê dois exemplos de dados derivados e diga de quais dados vieram.
