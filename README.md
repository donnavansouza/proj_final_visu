# Quem ficou para trás?

**A desigualdade da vacinação contra a Covid-19 nos 184 municípios do Ceará (2021–2024).**
Projeto final da disciplina de Visualização de Dados — Lucas Santos Maia e Donnavan Souza de Carvalho.

O produto é uma página web em narrativa rolável (*scrollytelling*), feita com HTML, CSS e
JavaScript puros, D3.js e Scrollama, publicada no GitHub Pages. A história é uma investigação:
os "suspeitos de sempre" (renda, interior, política, rede de saúde, hábito vacinal) são testados
e descartados; a reviravolta é que parte da desigualdade estava na própria medida; corrigida a
medida, aparecem os municípios que **começaram atrás e não conseguiram trazer as pessoas de volta
para a 2ª dose**.

---

## Por onde começar

**Tem pouco tempo?** Leia só o [docs/00-comece-aqui.md](docs/00-comece-aqui.md): a história, os números
e as decisões que vocês precisam saber explicar, num plano de 3 dias. O resto é para aprofundar.

| Documento | O que tem |
|---|---|
| [docs/00-comece-aqui.md](docs/00-comece-aqui.md) | **O essencial em 3 dias**: o que precisa dominar e o que pode tratar como caixa-preta |
| [docs/01-tecnico.md](docs/01-tecnico.md) | Como o site funciona: arquitetura, módulos, scrollytelling, interação, acessibilidade, desempenho, testes, publicação |
| [docs/02-dados.md](docs/02-dados.md) | De onde vem cada dado, como foi tratado, decisões, validações e limites |
| [docs/03-tipos-de-dados.md](docs/03-tipos-de-dados.md) | Tipos de dados e de atributos, escalas, codificação visual, cores, formatos de arquivo |
| [docs/04-metodos.md](docs/04-metodos.md) | Os métodos estatísticos usados, com intuição, fórmula e o resultado no projeto |
| [docs/05-guia-de-estudo.md](docs/05-guia-de-estudo.md) | Roteiro de estudo, perguntas para treinar a apresentação e sugestões de livros, cursos e artigos |
| [docs/06-inventario-dos-brutos.md](docs/06-inventario-dos-brutos.md) | Todo arquivo bruto usado: onde está, origem, como recuperar, hash SHA-256 e em que dado final se transformou |

---

## Ver o site no computador

O site lê arquivos JSON com `fetch`, o que o navegador bloqueia quando a página é aberta direto do
disco (`file://`). Use um servidor local:

```bash
python -m http.server 8000
# abra http://localhost:8000
```

No GitHub Pages funciona sem nada disso: *Settings → Pages → Deploy from a branch → main / (root)*.

## Estrutura

O projeto tem duas metades: **o site** (na raiz, porque é dali que o GitHub Pages publica) e
**a análise** (os dados, os scripts que os transformam e o que eles concluem). Os dados seguem
sempre o mesmo caminho: `dados/brutos/` → `pipeline/` → `dados/processados/` → `json/` → site.

```
O SITE
index.html                  a página (todos os capítulos)
css/style.css               identidade visual e layout
js/                         um arquivo por capítulo + util.js (funções comuns) + main.js (inicia tudo)
json/                       os dados que o site lê (gerados por pipeline/preparar_site.py)

A ANÁLISE
dados/
  brutos/                   como baixamos: nunca editados à mão
    vacinacao/              covid19br-vac (processed_CE) e influenza 2019
    microdados_CE/          recorte dos microdados do OpenDataSUS (491 MB; só local, fora do GitHub)
    ibge/                   Censo 2022 e estimativas (SIDRA)
    cnes/                   rede de saúde (estabelecimentos e equipes)
    tse/                    eleições 2016–2022 + SHA256SUMS.txt
    referencia/             lista de municípios (IDHM) e malha do mapa
  processados/              tabelas por município geradas pelo pipeline (.csv)
pipeline/                   os scripts Python, um por etapa (ordem abaixo)
relatorios/                 o que cada etapa concluiu e validou (.md)

APOIO
docs/                       documentação para estudo
testes/                     testes do site no navegador (puppeteer; só local, fora do GitHub)
```

## Refazer tudo, do bruto ao site

Requisitos: Python 3.11+ (`python -m pip install -r requirements.txt`). Todos os comandos rodam
**da raiz do projeto**. Um comando só refaz tudo o que dá para refazer com o repositório:

```bash
python pipeline/rodar_tudo.py
```

Ele executa, em ordem, as etapas 3 a 11 da tabela (cada etapa lê o que a anterior gravou):

| # | Script | Lê | Grava |
|---|---|---|---|
| 1 | `coleta_ibge_cnes.py` ¹ | API do IBGE, FTP do DATASUS | `dados/brutos/ibge/`, `dados/brutos/cnes/` |
| 2 | `base_municipal.py <PASTA_OBITOS>` ¹ | `dados/brutos/` (vacinação, IBGE, referência) | `dados/processados/municipal.csv` |
| 3 | `tse_municipal.py` | `dados/brutos/tse/` | `dados/processados/tse_municipal.csv` |
| 4 | `aps_censo.py` | `dados/brutos/cnes/`, `dados/brutos/ibge/`, etapa 2 | `dados/processados/aps_censo_municipal.csv` |
| 5 | `analise_politica.py` | etapas 2, 3, 4 | `dados/processados/base_analise.csv`, `relatorios/analise_politica.md` |
| 6 | `analise_eixos.py` | etapa 5 | `relatorios/analise_eixos.md` |
| 7 | `microdados_vacinacao.py filtrar <CSVs>` ¹ | 5 CSVs originais do OpenDataSUS | `dados/brutos/microdados_CE/` |
| 8 | `microdados_vacinacao.py agregar` e `series` ² | `dados/brutos/microdados_CE/` | `dados/processados/microdados_*.csv` |
| 9 | `verificacoes_finais.py` | etapas 5 e 8 | `relatorios/verificacoes_finais.md` |
| 10 | `preparar_site.py` | tudo acima | `json/*.json` |
| 11 | `auditar_cifras.py` | `json/`, etapa 9 | `relatorios/auditoria_cifras.md` |

¹ Dependem de arquivos de fora do repositório e não estão no `rodar_tudo.py`. O resultado delas já
está gravado. A etapa 2 precisa dos óbitos `cases_2020/2021/2022.csv.gz` (só serviam para a
mortalidade de 2020, já gravada em `municipal.csv`); a 7, dos 5 CSVs de ~2,7 GB do OpenDataSUS. Como
baixar e conferir cada um: [docs/06-inventario-dos-brutos.md](docs/06-inventario-dos-brutos.md).

² `dados/brutos/microdados_CE/` (491 MB) **não vai para o GitHub** (ver `.gitignore`): é pesado e são
registros individuais. Quem não o tem pula a etapa 8 e usa os CSVs já em `dados/processados/`; o
`rodar_tudo.py` faz isso sozinho.

## Créditos e fontes

OpenDataSUS / Ministério da Saúde (microdados de vacinação) · W. Cota, covid19br e covid19br-vac ·
IBGE (Censo 2022, estimativas 2021, SIDRA) · TSE (resultados 2016–2022) · CNES / DATASUS ·
SI-PNI (influenza 2019) · Atlas Brasil (IDHM 2010) · geodata-br (malha municipal).
Bibliotecas: D3 7.9.0, Scrollama 3.2.0, noUiSlider 15.7.1, Tom Select 2.3.1, fontes Fraunces e
Source Sans 3 (Google Fonts).
