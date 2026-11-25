# 2. Os dados: de onde vêm, como foram tratados e o que não dizem

> Lista completa dos arquivos brutos, com origem e hash: [06-inventario-dos-brutos.md](06-inventario-dos-brutos.md).
>
> Este documento conta a vida de cada dado: a fonte, o arquivo, o que foi feito com ele e as decisões
> que mudaram o resultado. Ao final: dicionário das tabelas principais e perguntas de revisão.

## 2.1 Unidade de análise e chave

- **Unidade:** o município (184 no Ceará). Nenhum dado individual é mostrado ou analisado como pessoa —
  os microdados de vacinação são agregados por município antes de qualquer análise.
- **Chave:** código IBGE de **7 dígitos, sempre como texto** (`"2304400"` é Fortaleza). Como número,
  um código que começa com zero perderia o zero; como texto, nunca. Algumas fontes usam **6 dígitos**
  (sem o dígito verificador: `230440`) e o TSE usa um **código próprio de 5 dígitos** (`13897`).
  Nunca cruzamos por nome de município (acentos e grafias variam).
- **Regra de toda junção:** conferir que saíram 184 linhas, sem duplicatas.

## 2.2 As fontes

### 1. Vacinação: microdados do OpenDataSUS

| | |
|---|---|
| **O quê** | Um registro por dose aplicada: paciente (identificador anonimizado), idade, sexo, município de residência, estabelecimento e seu município, data, dose, vacina |
| **Onde** | Portal de Dados Abertos do SUS (antigo OpenDataSUS, hoje `dadosabertos.saude.gov.br`), conjunto *Registros de Vacinação COVID19*. Baixamos os arquivos do **Ceará** (5 CSVs de ~2,7 GB, ~27,9 milhões de linhas) |
| **Script** | `pipeline/microdados_vacinacao.py` — etapas `filtrar`, `agregar`, `series` |
| **Período** | 17/01/2021 a 16/04/2024 (o mesmo da base `processed_CE`, para comparar) |

Tratamento, na ordem:
1. Leitura em blocos de 500 mil linhas, guardando só 9 colunas (o arquivo inteiro não cabe na memória).
2. **Só vacinas Covid:** a base traz também influenza (`INF3`) — **2.184.834** registros excluídos.
3. **Só o período:** 131.617 doses fora de 17/01/2021–16/04/2024 excluídas (há datas de 2002, erros de digitação).
4. **Duplicatas exatas** removidas: 101.160.
5. **Classificação da dose** (na agregação) (`vacina_descricao_dose` tem 24 valores diferentes): "1ª Dose" → D1;
   "2ª Dose" → D2; "Única" e "Dose" → DU (dose única, Janssen); reforços, adicionais, 3ª dose em diante →
   REF. A tabela completa está em `relatorios/microdados_validacao.md`.
6. **Pessoas, não doses:** o identificador do paciente (convertido em um código numérico de 64 bits,
   para caber na memória) permite contar **pessoas distintas**. Há em média 1,03 registro de 1ª dose
   por pessoa no estado — e 1,55 em Itaiçaba.
7. **Residência, não aplicação:** cada pessoa é atribuída ao município de residência informado na sua
   1ª dose.

Resultado: **24.403.625 doses** aplicadas a residentes do Ceará; 7,93 milhões de pessoas com 1ª dose
(ou dose única) e 6,91 milhões com esquema completo.

**O recorte local:** `dados/brutos/microdados_CE/` (só no computador, fora do GitHub) guarda as ~27,9 milhões de linhas filtradas pela
etapa 1 (antes dos passos 2–4, que acontecem na agregação), em 5 partes `.csv.gz` (491 MB no total).
Para caber, ficam só as 6 colunas usadas (`paciente_id`, `res_ibge`, `est_ibge`, `data`, `dose`, `vacina`)
e o identificador do paciente truncado em 16 caracteres hexadecimais (64 bits). O identificador original
já é um código anonimizado de 64 caracteres; com ~9 milhões de pessoas, a chance de duas colidirem nos
64 bits é da ordem de 1 em 500 mil. Conferimos: as tabelas geradas a partir do recorte compacto são
idênticas às geradas a partir do recorte completo. Os 5 arquivos originais (13,4 GB) não ficam no
repositório.

### 2. Vacinação agregada: covid19br-vac (Wesley Cota)

| | |
|---|---|
| **O quê** | Doses por dia × município × dose × fabricante × sexo × faixa etária, já agregadas a partir do OpenDataSUS |
| **Onde** | `github.com/wcota/covid19br-vac` → `dados/brutos/vacinacao/processed_CE.csv.gz` |
| **Uso** | Base da primeira fase do projeto (`pipeline/base_municipal.py` → `dados/processados/municipal.csv`). Hoje serve de comparação e para o estado (a) do capítulo 3 |

O que descobrimos: (i) ela conta por **município de residência** (bate com os microdados em 118 de 184
municípios, diferença mediana de 0,7%); (ii) tem **2.528 linhas sem data** (12.860 doses, quase todas
de 1ª dose), concentradas na Região Metropolitana; (iii) total de 24.673.571 doses. A documentação do
repositório não dizia (i) nem (ii); foi preciso testar.

### 3. População: IBGE

| Dado | Fonte | Uso |
|---|---|---|
| Estimativa 2021 (`pop2021`) | IBGE, vem embutida no `processed_CE` | Denominador "antigo"; só no estado (a) do capítulo 3 |
| Censo 2022 (`pop2022`) | SIDRA, tabela 9923 | **Denominador principal** |

A estimativa de 2021 superava o Censo em 4,8% no estado (9.240.580 contra 8.794.957) e errava muito
em alguns municípios: Catarina tinha menos da metade da população estimada (razão 0,49); Itaitinga,
67% a mais (64.650 contra 38.661). Esse erro, sozinho, criava "piores" e "melhores" falsos.

### 4. Censo 2022: características dos municípios (SIDRA / IBGE)

Coletadas por `pipeline/coleta_ibge_cnes.py` pela **API de agregados v3** do IBGE
(`servicodados.ibge.gov.br/api/v3/agregados`), que permite pedir as categorias abertas — a primeira
exportação manual pelo site do SIDRA veio só com "Total".

| Tabela | Variável usada |
|---|---|
| 9543 | Taxa de alfabetização, 15 anos ou mais |
| 10061 | Nível de instrução, 18+ (% superior completo; % sem instrução/fundamental incompleto) |
| 10295 | Rendimento domiciliar per capita **mediano** e médio |
| 9537 | Religião, 10+ (% católicos, evangélicos, sem religião) |
| 9942 | Moradores sem conexão domiciliar à internet (%) |
| 9923 | População residente total, urbana e rural |

Detalhe: no SIDRA, `-` significa **zero absoluto** (ex.: população rural de Fortaleza) e `...`
significa **não disponível**. Tratar os dois como vazio é um erro comum.

### 5. Eleições: TSE

Arquivos em `dados/brutos/tse/` (compactados, com `SHA256SUMS.txt`), processados por `pipeline/tse_municipal.py`.

| Arquivo | Para quê |
|---|---|
| `votacao_candidato_munzona_2018_BR`, `…_2022_BR` | Presidente, 1º e 2º turnos. **Presidente fica no arquivo `_BR`**, não no `_CE` |
| `votacao_candidato_munzona_2020_CE` | Prefeito eleito, % de votos, margem, partido |
| `detalhe_votacao_munzona_2018_BR`, `…_2022_BR` | Comparecimento, brancos e nulos |
| `consulta_cand_2016_CE`, `…_2020_CE` | Reeleição: o prefeito eleito em 2020 também foi eleito em 2016? |
| `municipio_tse_ibge.zip` | Tabela oficial de correspondência código TSE → código IBGE |

Validação: totais do 2º turno batem com o resultado oficial (Haddad 71,11% em 2018; Lula 69,97% em
2022). Comparecimento no 2º turno: 81,3% (2018) e 82,9% (2022). Reeleitos em 2020: 65 de 178.
Seis municípios ficaram sem prefeito eleito na eleição ordinária de 2020 (candidaturas indeferidas
e eleições suplementares) — sinalizados, não descartados.

> **Dados pessoais:** os arquivos `consulta_cand` contêm CPF e e-mail dos candidatos. São dados
> públicos do TSE e foram usados só para ligar o prefeito de 2020 ao de 2016 — nenhum identificador
> vai para as saídas. Antes de tornar o repositório público, vale decidir se esses dois arquivos
> devem ir junto.

### 6. Rede de saúde: CNES / DATASUS

Arquivos `.dbc` do FTP do DATASUS (`ST` = estabelecimentos, `EP` = equipes), dez/2020 e dez/2021,
baixados por `pipeline/coleta_ibge_cnes.py`. O formato `.dbc` é um `.dbf` comprimido com o algoritmo *implode* da
PKWare; o leitor usual em Python (`pyreaddbc`) não instalava no Windows com Python 3.14, então
escrevemos um descompressor em Python puro dentro do `pipeline/coleta_ibge_cnes.py`.

Indicadores (`pipeline/aps_censo.py`): UBS (tipos 01 e 02) e equipes de Saúde da Família ativas
(tipo 70) por 10 mil habitantes. Em dez/2021: 2.526 UBS e 2.858 eSF no estado. A "cobertura estimada
da atenção primária" (equipes × 3.450 pessoas) satura em 100% em 180 municípios e por isso não foi usada.

### 7. Outros

| Dado | Fonte | Observação |
|---|---|---|
| Óbitos por Covid 2020 | covid19br (W. Cota), `cases-brazil-cities-time_AAAA.csv.gz` (fora do repositório; ver [inventário](06-inventario-dos-brutos.md#62-óbitos-por-covid-removidos-do-repositório)) | Data de **divulgação**, não de ocorrência |
| Vacina da gripe 2019, idosos | SI-PNI (`dados/brutos/vacinacao/coberturaVacinalInfluenza_2019.csv`) | Arquivo **sem cabeçalho**; colunas identificadas pela ordem de grandeza. 162 de 184 municípios com ≥ 90% |
| IDHM 2010 | Atlas Brasil (`dados/brutos/referencia/municipios.csv`) | Substituído pela renda do Censo 2022 nos controles |
| Malha municipal | geodata-br (`dados/brutos/referencia/geojs-23-mun.json`) | 184 polígonos; `properties.id` = IBGE 7 dígitos. Também gera a lista de **vizinhos** |

## 2.3 As decisões que mudaram o resultado

| Decisão | Alternativa | Por que escolhemos | Efeito |
|---|---|---|---|
| Denominador = Censo 2022 | Estimativa 2021 | O Censo conta; a estimativa projeta | Fortaleza deixa de estar "atrás"; Catarina sai do último lugar (50% → 102% de 1ª dose) |
| Contar **pessoas** | Contar doses | A mesma pessoa aparece com mais de uma 1ª dose | Municípios acima de 100% de 1ª dose: 60 → 41 |
| Município de **residência** | De aplicação | O campo de aplicação registra muitas doses do interior em estabelecimentos de Fortaleza (Fortaleza teria 219%) | Coberturas plausíveis |
| Abandono **individual** | Agregado (1 − D2/D1) | O agregado mistura pessoas diferentes e chegava a ser negativo | 9 municípios com abandono negativo → nenhum |
| Período fixo 17/01/21–16/04/24 | Tudo o que há no arquivo | Comparabilidade com `processed_CE` | — |
| Manter valores > 100% | Cortar em 100% | Excesso é informação sobre a medida | Teto só na escala de cor, com alerta visual |

## 2.4 Validações feitas

- 184 municípios em toda junção; códigos únicos.
- Totais eleitorais contra o resultado oficial do TSE.
- Série semanal × totais por município: diferença zero (mesmas definições nas duas etapas).
- **Auditoria das cifras do site** (`pipeline/auditar_cifras.py` → `relatorios/auditoria_cifras.md`):
  23 números conferidos contra `verificacoes_finais.md`, nenhum diferente.
- Excesso de pessoas acima da população recalculado no preparo do site e comparado com as verificações
  (49.473) por `assert`.

## 2.5 O que os dados não dizem (limites)

1. **Falácia ecológica:** correlação entre municípios não diz nada sobre pessoas. "Municípios com mais
   voto em X vacinaram menos" ≠ "eleitores de X se vacinaram menos".
2. **Nada causal:** análise exploratória, 184 observações, sem desenho que isole causas.
3. **Temporalidade:** 2018 é antes da pandemia; 2020, durante; 2022 depois do grosso da vacinação —
   não pode ser causa da vacinação de 2021.
4. **Medida:** mesmo corrigida, sobram 41 municípios com mais pessoas vacinadas que moradores (cadastro
   de residência desatualizado, migração). Itaitinga é **sensível ao denominador**: os dados não decidem
   se a cobertura é 112% ou 67%.
5. **O que não medimos:** gestão local da campanha, busca ativa de faltosos, qualidade do registro.

## 2.6 Dicionário das tabelas principais

### `dados/processados/microdados_municipal.csv` (184 linhas; base do site)

| Coluna | Significado |
|---|---|
| `ibge` | Código IBGE, 7 dígitos (texto) |
| `d1_res`, `d2_res`, `du_res`, `ref_res` | Doses por residência: 1ª, 2ª, única, reforços |
| `d1_apl`, … | As mesmas, por município de aplicação (não usar para cobertura) |
| `pessoas_d1` | Pessoas distintas com 1ª dose (residência da 1ª dose) |
| `com_d2` | Dessas, quantas têm 2ª dose |
| `abandono_individual` | 1 − `com_d2` / `pessoas_d1` |
| `saldo_importacao` | (doses aplicadas − doses de residentes) / doses de residentes |
| `pct_doses_residentes_no_proprio_mun` | Doses de residentes aplicadas no próprio município |

Derivadas no site: **1ª dose** = (`pessoas_d1` + `du_res`) ÷ `pop2022`; **esquema completo** =
(`com_d2` + `du_res`) ÷ `pop2022`; **reforço** = `ref_res` ÷ `pop2022` (doses por habitante).

### `dados/processados/base_analise.csv`

`dados/processados/municipal.csv` + `tse_municipal.csv` + `aps_censo_municipal.csv`, uma linha por município. Colunas de
controle: `log_pop2022`, `log_densidade`, `razao_pop22_21` (erro da estimativa), `alfab15`,
`renda_mediana_pc`. Políticas: `pct_bolsonaro_2018`, `var_bolsonaro_18_22` etc.

### `json/*.json` (site)

| Arquivo | Conteúdo |
|---|---|
| `geo.json` | Malha simplificada (3 casas decimais) |
| `cap1.json` | Série semanal do estado e faixa P10–P90; doses diárias; marcos |
| `cap2.json` | Esquema completo e as 5 hipóteses por município; correlações |
| `cap3.json` | 1ª dose nos três estados (a, b, c) por município; contagens; destaques |
| `cap4.json` | Os 13, perfis, decomposição, I de Moran, valores dos três mapas |
| `cap5.json` | Reforço por habitante e variação do voto; percentis; R² |
| `cap7.json` | 13 variáveis + série mensal por município (Explore) |

## Perguntas de revisão

1. Por que o código IBGE é guardado como texto?
2. Qual a diferença entre contar doses e contar pessoas, e qual erro cada uma evita ou comete?
3. Como descobrimos que o `processed_CE` usa o município de residência?
4. Por que o campo "município de aplicação" não serve para medir cobertura?
5. O que significa `-` numa tabela do SIDRA? E `...`?
6. Por que Itaitinga é "sensível ao denominador" e não "o pior do estado"?
7. Explique a falácia ecológica com um exemplo do próprio projeto.
