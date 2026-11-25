# 6. Inventário dos dados brutos

> Todos os arquivos brutos que geraram os dados finais: onde estão, de onde vieram, como recuperar e
> em que se transformaram. O **hash SHA-256** é a "impressão digital" do arquivo: se um arquivo baixado
> de novo tiver o mesmo hash, é exatamente o mesmo conteúdo usado aqui.
>
> Conferir um hash: `sha256sum arquivo` (Git Bash/Linux/Mac) ou `Get-FileHash arquivo` (PowerShell).

Legenda de **Onde**: 📁 no repositório (vai para o GitHub) · 💻 só no computador local (está no `.gitignore`) ·
☁️ fora do projeto (recuperar pela origem).

## 6.1 Vacinação

| Arquivo | Onde | Origem | Vira | SHA-256 |
|---|---|---|---|---|
| 5 CSVs originais `part-0000{0..4}-0656f017-…c000.csv` (~2,7 GB cada, só CE) | ☁️ | Portal de Dados Abertos do SUS (`dadosabertos.saude.gov.br`) → *Registros de Vacinação COVID19* → arquivos do Ceará. Baixados em 12/11/2026 | `dados/brutos/microdados_CE/` (etapa `filtrar`) | não registrado¹ |
| `dados/brutos/microdados_CE/parte_part-00000-…csv.gz` | 💻 | Recorte compacto dos originais | `dados/processados/microdados_*.csv` (etapas `agregar` e `series`) | `fc69c6fa3cc7001b3e134f47d003fd1675ffb0222d8ea1c4184bef186f981d70` |
| `…parte_part-00001-…csv.gz` | 💻 | idem | idem | `f97a7c16dfb326484000e1f70239d57d5e87716300e1d3be1fd688a83a534a16` |
| `…parte_part-00002-…csv.gz` | 💻 | idem | idem | `40b42d89d2254fb2bb297e48e6dc6c6e9e92c7ea6c6bb13ce3ab494e692cbf4e` |
| `…parte_part-00003-…csv.gz` | 💻 | idem | idem | `f3a07258dd76fdc78ffa76b0287c642e16dc4fbd561ae60011f1fb091a013fb4` |
| `…parte_part-00004-…csv.gz` | 💻 | idem | idem | `c2afa240de02cec7c1d5144d8be1e60afbeb1b1fd4424332b706fde35b2fb649` |
| `dados/brutos/vacinacao/processed_CE.csv.gz` | 📁 | [github.com/wcota/covid19br-vac](https://github.com/wcota/covid19br-vac) → `https://raw.githubusercontent.com/wcota/covid19br-vac/main/processed_CE.csv.gz` | `dados/processados/municipal.csv` (`pipeline/base_municipal.py`): doses e população estimada 2021 | `28ed64d1fa1c1734c250861a5ea1247057932d5865ab073ae9942a4aee6e130f` |
| `dados/brutos/vacinacao/coberturaVacinalInfluenza_2019.csv` | 📁 | SI-PNI / DATASUS, campanha de influenza 2019, exportação por município (sem cabeçalho) | `dados/processados/municipal.csv`: `flu_idosos_cob` (suspeito "o hábito") | `0915e0fc780aab13840b44cf58e2e46b25d4fa288b1ced9cf477fbf96fc7939e` |

¹ Os originais não tiveram o hash registrado no download. O portal é atualizado periodicamente, então
uma nova cópia pode diferir; o recorte (com os hashes acima) é a referência. O recorte fica só no
computador local: tem 491 MB e são registros individuais, então não vai para o GitHub. Quem o tem pode
passá-lo por um pendrive ou pelo OneDrive e conferir os hashes; quem não tem usa os totais já gravados em
`dados/processados/microdados_*.csv`, que bastam para gerar o site.

## 6.2 Óbitos por Covid (removidos do repositório)

Usados só para a mortalidade de 2020 por 100 mil habitantes (hipótese do histórico sanitário, resultado
nulo). O valor calculado já está no `dados/processados/municipal.csv`; os arquivos só são necessários para rodar o
`pipeline/base_municipal.py` do zero.

| Arquivo | Onde | Recuperar | Tamanho | SHA-256 |
|---|---|---|---|---|
| `cases-brazil-cities-time_2020.csv.gz` | ☁️ | `https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-cities-time_2020.csv.gz` | 30.244.467 bytes | `e381ba93aa1d36dc39bdf451d96fc253a96f95f070ddaeebde2cd7ac2e33e256` |
| `cases-brazil-cities-time_2021.csv.gz` | ☁️ | `…/cases-brazil-cities-time_2021.csv.gz` | 53.556.046 bytes | `26b4fd04d29d4603b7cbeb5fd71f6984880bff74a2ca8369da5487464454ea5f` |
| `cases-brazil-cities-time_2022.csv.gz` | ☁️ | `…/cases-brazil-cities-time_2022.csv.gz` | 54.524.659 bytes | `5334891fc48bf38e00d6fe71394073fd8a46decfa965289aa626ca914e055072` |

Para recuperar (o `pipeline/base_municipal.py` espera os nomes `cases_AAAA.csv.gz` numa pasta qualquer,
passada como argumento; aqui, `obitos/`, que é temporária e pode ser apagada depois):

```bash
mkdir obitos
for a in 2020 2021 2022; do
  curl -L -o obitos/cases_$a.csv.gz "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-cities-time_$a.csv.gz"
done
sha256sum obitos/cases_*.csv.gz        # conferir com a tabela acima
python pipeline/base_municipal.py obitos   # grava dados/processados/municipal.csv
```

O repositório covid19br foi descontinuado em março de 2023, então os arquivos de 2020–2022 não devem
mudar; se o hash não bater, a análise pode ter números um pouco diferentes de mortalidade.

## 6.3 População e Censo 2022 (IBGE)

| Arquivo | Onde | Origem | Vira | SHA-256 |
|---|---|---|---|---|
| `dados/brutos/ibge/tabela9923.csv` | 📁 | SIDRA, tabela 9923 (população residente 2022), exportação manual em CSV | `dados/processados/municipal.csv`: `pop2022` | `a11cec6af63646d96fed6f181eb2d6ff976ad1ba97615447ec8ac2c0aecd50e3` |
| `dados/brutos/ibge/tabela9543.csv` | 📁 | SIDRA, tabela 9543 (alfabetização 15+) | `dados/processados/municipal.csv`: `alfab15` | `7632130e45f84449c5a2f5782038c75c07fa20a5f953eba823ef703b58aa9879` |
| `dados/brutos/ibge/tabela10061.csv` | 📁 | SIDRA, tabela 10061 (população 18+) | `dados/processados/municipal.csv`: `pop18_2022` | `bbcac9866647c9ca426e40e1c7d57130d7b6488b5627758da459e534ca520d56` |
| `dados/brutos/ibge/sidra_10295.csv` | 📁 | API de agregados do IBGE (`pipeline/coleta_ibge_cnes.py`), tabela 10295 | `aps_censo_municipal.csv`: renda mediana e média | `5944373a6b840ca8c5521906eb27a77259da2338d7ddd5f0917a73c61808615c` |
| `dados/brutos/ibge/sidra_10061.csv` | 📁 | idem, tabela 10061 com níveis de instrução | % superior completo, % sem fundamental | `d2e0d1d20dff7b9eb390c404006fc86e86427ac2949599fea16c486b2bbe3f6a` |
| `dados/brutos/ibge/sidra_9537.csv` | 📁 | idem, tabela 9537 (religião) | % católicos, evangélicos, sem religião | `b270b52d8f68fa58bbffe5ccfaccc8df40ebc0079bdb4c0d6addab070138546d` |
| `dados/brutos/ibge/sidra_9942.csv` | 📁 | idem, tabela 9942 (internet) | % sem internet | `bc3eb179e9423010c265ef74ec0aa2b8723635b452b50b33185484e30c5609b4` |
| `dados/brutos/ibge/sidra_9923.csv` | 📁 | idem, tabela 9923 (urbana/rural) | % rural | `e66f7a0ee76a441ffc891f7f657cda84c6706754520b97d51021b0c80153aeac` |

As consultas exatas à API estão em `dados/brutos/log_coleta.txt`. Recuperar: `python pipeline/coleta_ibge_cnes.py sidra`.

## 6.4 Rede de saúde (CNES / DATASUS)

| Arquivo | Onde | Origem | Vira | SHA-256 |
|---|---|---|---|---|
| `STCE2012.dbc`, `STCE2112.dbc`, `EPCE2012.dbc`, `EPCE2112.dbc` | ☁️ | FTP `ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/{ST,EP}/` | Convertidos em `dados/brutos/cnes/cnes_*.csv` | registrados em `dados/brutos/log_coleta.txt`² |
| `dados/brutos/cnes/cnes_STCE2012.csv` | 📁 | Conversão do `.dbc` por `pipeline/coleta_ibge_cnes.py` | `aps_censo_municipal.csv`: UBS por 10 mil | `3e053780458c1df7a77a75bc8792aa7316c42e03f8177a708bac3150828c7330` |
| `dados/brutos/cnes/cnes_STCE2112.csv` | 📁 | idem | idem | `a206ae3ec27e391097adecc28a7cd96182eee850f81f738710d377a96be3727d` |
| `dados/brutos/cnes/cnes_EPCE2012.csv` | 📁 | idem | equipes de Saúde da Família por 10 mil | `77621de169333afa57bd322c31f6a724c716844d99742afdff2990b48e35f257` |
| `dados/brutos/cnes/cnes_EPCE2112.csv` | 📁 | idem | idem | `33eaca36206ad75e1f985aba2dd2c3aa4d08a44a8f9b2586859dcdc4a15f05f4` |

² Hashes dos `.dbc` baixados (copiados de `dados/brutos/log_coleta.txt`):

| Arquivo | Bytes | SHA-256 |
|---|---|---|
| `STCE2012.dbc` | 541.950 | `ccb4cf745f34088b645e24d3f8a4c08b9b4c3c100219a93908d3ade2c85a99c6` |
| `STCE2112.dbc` | 577.544 | `e5d12ab7249cb53b2ceb3976db73e7a72dd5205a6f549e423af0df8256eadd6f` |
| `EPCE2012.dbc` | 180.880 | `43ef054ac5622b3ca7a5541c555e26eb26004f99009f7e34c539b55699e0ad48` |
| `EPCE2112.dbc` | 185.682 | `1fc16a7c9307b7245c31e2924fd516eb3f02ec58352f8796274ff9959fd879fa` |

Recuperar: `python pipeline/coleta_ibge_cnes.py cnes`.

## 6.5 Eleições (TSE)

Todos em `dados/brutos/tse/` (📁), com os hashes completos em `dados/brutos/tse/SHA256SUMS.txt`. Origem: zips de
[dadosabertos.tse.jus.br](https://dadosabertos.tse.jus.br) (resultados 2018, 2020, 2022; candidatos
2016 e 2020; códigos de municípios TSE–IBGE), dos quais extraímos só os CSVs usados.

| Arquivo | Vira (`dados/processados/tse_municipal.csv`) |
|---|---|
| `votacao_candidato_munzona_2018_BR.csv.gz`, `…_2022_BR.csv.gz` | Voto em Bolsonaro (1º e 2º turnos), variação 2018→2022 |
| `votacao_candidato_munzona_2020_CE.csv.gz` | Prefeito eleito, partido, % de votos, margem |
| `detalhe_votacao_munzona_2018_BR.csv.gz`, `…_2022_BR.csv.gz` | Comparecimento, brancos e nulos |
| `consulta_cand_2016_CE.csv.gz`, `consulta_cand_2020_CE.csv.gz` | Reeleição do prefeito (contêm CPF e e-mail de candidatos) |
| `municipio_tse_ibge.zip` | Correspondência código TSE → IBGE |

## 6.6 Bases municipais e malha

| Arquivo | Onde | Origem | Vira | SHA-256 |
|---|---|---|---|---|
| `dados/brutos/referencia/geojs-23-mun.json` | 📁 | [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br) → `geojson/geojs-23-mun.json` (malha IBGE) | `json/geo.json`; área, distância a Fortaleza e vizinhos em `dados/processados/municipal.csv` | `5d29d19663f43a723b19fbd5d255b06d682f9cd2dd74b92de3ec1153676bdd66` |
| `dados/brutos/referencia/municipios.csv` | 📁 | Tabela da primeira versão do projeto (Colab); colunas de IDHM 2010 do [Atlas Brasil](http://www.atlasbrasil.org.br) | `dados/processados/municipal.csv`: nomes e IDHM | `7fa7238c1b80c22d6acc28c54bc6e9a2db2fecc7821f95c85a07617aab3215bf` |

## 6.7 Do bruto ao final (resumo)

```
microdados (☁️) ─filtrar─► dados/brutos/microdados_CE (💻) ─agregar/series─► processados/microdados_*.csv ─┐
brutos/vacinacao, brutos/ibge, brutos/referencia ─base_municipal.py─► processados/municipal.csv ──────────┤
brutos/tse ─tse_municipal.py─► processados/tse_municipal.csv ────────────────────────────────────────────┤
brutos/cnes, brutos/ibge ─aps_censo.py─► processados/aps_censo_municipal.csv ─────────────────────────────┤
                                                                                                          ▼
                   analise_politica.py → processados/base_analise.csv → analise_eixos.py, verificacoes_finais.py
                                                                                                          ▼
                                                                   preparar_site.py → json/*.json → site
```
