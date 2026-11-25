# Eixo político × vacinação — resultados exploratórios

n = 184 municípios; sem alerta (pop2021) = 133; sem alerta (Censo) = 117.
Controles da correlação parcial: log_pop2022, log_densidade, alfab15, renda_mediana_pc (renda_mediana_pc = rendimento domiciliar per capita mediano, Censo 2022).

## 1. Spearman simples e parcial (todos os municípios)

| Variável política | Desfecho | ρ | p | ρ parcial | p parcial | ρ parcial + erro de pop. | q (FDR, parcial+pop) |
|---|---|---|---|---|---|---|---|
| Bolsonaro 2º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.20 | 0.006 | -0.04 | 0.588 | -0.03 | 0.772 |
| Bolsonaro 2º t. 2018 (%) | Esquema completo final | -0.21 | 0.004 | -0.06 | 0.390 | -0.05 | 0.678 |
| Bolsonaro 2º t. 2018 (%) | Reforços por hab. (final) | -0.27 | 0.000 | -0.07 | 0.317 | -0.07 | 0.625 |
| Bolsonaro 2º t. 2018 (%) | Abandono aproximado | +0.04 | 0.564 | -0.01 | 0.914 | -0.01 | 0.892 |
| Bolsonaro 2º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.08 | 0.305 | +0.05 | 0.478 | +0.06 | 0.632 |
| Bolsonaro 1º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.25 | 0.001 | -0.11 | 0.131 | -0.11 | 0.454 |
| Bolsonaro 1º t. 2018 (%) | Esquema completo final | -0.26 | 0.000 | -0.12 | 0.104 | -0.12 | 0.444 |
| Bolsonaro 1º t. 2018 (%) | Reforços por hab. (final) | -0.36 | 0.000 | -0.20 | 0.008 | -0.20 | 0.159 |
| Bolsonaro 1º t. 2018 (%) | Abandono aproximado | +0.09 | 0.225 | +0.07 | 0.334 | +0.07 | 0.625 |
| Bolsonaro 1º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.14 | 0.066 | +0.16 | 0.030 | +0.17 | 0.207 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Esquema completo dez/21 (ritmo) | -0.21 | 0.004 | -0.05 | 0.467 | -0.05 | 0.678 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Esquema completo final | -0.21 | 0.004 | -0.07 | 0.372 | -0.07 | 0.632 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Reforços por hab. (final) | -0.34 | 0.000 | -0.17 | 0.024 | -0.17 | 0.207 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Abandono aproximado | +0.07 | 0.330 | +0.03 | 0.723 | +0.03 | 0.772 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.12 | 0.107 | +0.10 | 0.179 | +0.10 | 0.474 |
| Variação 2018→2022 (pp) [posterior] | Esquema completo dez/21 (ritmo) | -0.12 | 0.114 | -0.10 | 0.194 | -0.12 | 0.444 |
| Variação 2018→2022 (pp) [posterior] | Esquema completo final | -0.10 | 0.165 | -0.08 | 0.308 | -0.09 | 0.538 |
| Variação 2018→2022 (pp) [posterior] | Reforços por hab. (final) | -0.32 | 0.000 | -0.30 | 0.000 | -0.31 | 0.001 |
| Variação 2018→2022 (pp) [posterior] | Abandono aproximado | +0.13 | 0.076 | +0.11 | 0.137 | +0.12 | 0.444 |
| Variação 2018→2022 (pp) [posterior] | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.19 | 0.012 | +0.16 | 0.033 | +0.15 | 0.291 |
| Votos do prefeito eleito 2020 (%) | Esquema completo dez/21 (ritmo) | -0.09 | 0.252 | -0.11 | 0.140 | -0.11 | 0.474 |
| Votos do prefeito eleito 2020 (%) | Esquema completo final | -0.07 | 0.339 | -0.09 | 0.240 | -0.08 | 0.580 |
| Votos do prefeito eleito 2020 (%) | Reforços por hab. (final) | -0.11 | 0.145 | -0.13 | 0.079 | -0.13 | 0.444 |
| Votos do prefeito eleito 2020 (%) | Abandono aproximado | +0.02 | 0.809 | +0.04 | 0.603 | +0.04 | 0.772 |
| Votos do prefeito eleito 2020 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | -0.01 | 0.868 | +0.02 | 0.798 | +0.03 | 0.772 |
| Margem do prefeito 2020 (pp) | Esquema completo dez/21 (ritmo) | -0.14 | 0.062 | -0.14 | 0.070 | -0.12 | 0.444 |
| Margem do prefeito 2020 (pp) | Esquema completo final | -0.11 | 0.127 | -0.10 | 0.186 | -0.08 | 0.580 |
| Margem do prefeito 2020 (pp) | Reforços por hab. (final) | -0.21 | 0.005 | -0.19 | 0.011 | -0.19 | 0.198 |
| Margem do prefeito 2020 (pp) | Abandono aproximado | +0.02 | 0.827 | +0.03 | 0.652 | +0.03 | 0.772 |
| Margem do prefeito 2020 (pp) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.03 | 0.663 | +0.06 | 0.455 | +0.07 | 0.625 |
| Prefeito reeleito em 2020 (0/1) | Esquema completo dez/21 (ritmo) | +0.11 | 0.147 | +0.10 | 0.173 | +0.09 | 0.548 |
| Prefeito reeleito em 2020 (0/1) | Esquema completo final | +0.08 | 0.301 | +0.07 | 0.333 | +0.06 | 0.645 |
| Prefeito reeleito em 2020 (0/1) | Reforços por hab. (final) | +0.01 | 0.848 | +0.00 | 0.977 | -0.00 | 0.959 |
| Prefeito reeleito em 2020 (0/1) | Abandono aproximado | +0.04 | 0.629 | +0.05 | 0.517 | +0.05 | 0.678 |
| Prefeito reeleito em 2020 (0/1) | Dia em que D1 chegou a 50% (menor = mais rápido) | -0.14 | 0.066 | -0.09 | 0.236 | -0.10 | 0.483 |
| Comparecimento 2º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.13 | 0.085 | +0.03 | 0.657 | +0.03 | 0.772 |
| Comparecimento 2º t. 2018 (%) | Esquema completo final | -0.10 | 0.194 | +0.05 | 0.477 | +0.05 | 0.710 |
| Comparecimento 2º t. 2018 (%) | Reforços por hab. (final) | -0.18 | 0.012 | -0.02 | 0.740 | -0.03 | 0.772 |
| Comparecimento 2º t. 2018 (%) | Abandono aproximado | +0.11 | 0.152 | +0.04 | 0.640 | +0.04 | 0.772 |
| Comparecimento 2º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.09 | 0.240 | +0.08 | 0.280 | +0.08 | 0.618 |

## 2. Estabilidade: ρ simples por amostra

| Variável política | Desfecho | todos | sem alerta | sem alerta (Censo) |
|---|---|---|---|---|
| Comparecimento 2º t. 2018 (%) | Abandono aproximado | +0.11 | +0.13 | +0.08 |
| Comparecimento 2º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.13 | -0.21 | -0.20 |
| Comparecimento 2º t. 2018 (%) | Esquema completo final | -0.10 | -0.18 | -0.18 |
| Comparecimento 2º t. 2018 (%) | Reforços por hab. (final) | -0.18 | -0.30 | -0.30 |
| Comparecimento 2º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.09 | +0.24 | +0.19 |
| Bolsonaro 1º t. 2018 (%) | Abandono aproximado | +0.09 | +0.18 | +0.10 |
| Bolsonaro 1º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.25 | -0.31 | -0.22 |
| Bolsonaro 1º t. 2018 (%) | Esquema completo final | -0.26 | -0.36 | -0.29 |
| Bolsonaro 1º t. 2018 (%) | Reforços por hab. (final) | -0.36 | -0.39 | -0.34 |
| Bolsonaro 1º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.14 | +0.21 | +0.12 |
| Bolsonaro 2º t. 2018 (%) | Abandono aproximado | +0.04 | +0.09 | +0.04 |
| Bolsonaro 2º t. 2018 (%) | Esquema completo dez/21 (ritmo) | -0.20 | -0.26 | -0.16 |
| Bolsonaro 2º t. 2018 (%) | Esquema completo final | -0.21 | -0.29 | -0.22 |
| Bolsonaro 2º t. 2018 (%) | Reforços por hab. (final) | -0.27 | -0.32 | -0.28 |
| Bolsonaro 2º t. 2018 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.08 | +0.16 | +0.06 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Abandono aproximado | +0.07 | +0.16 | +0.09 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Esquema completo dez/21 (ritmo) | -0.21 | -0.27 | -0.18 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Esquema completo final | -0.21 | -0.31 | -0.25 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Reforços por hab. (final) | -0.34 | -0.38 | -0.34 |
| Bolsonaro 2º t. 2022 (%) [posterior] | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.12 | +0.20 | +0.09 |
| Margem do prefeito 2020 (pp) | Abandono aproximado | +0.02 | +0.04 | -0.03 |
| Margem do prefeito 2020 (pp) | Esquema completo dez/21 (ritmo) | -0.14 | -0.11 | -0.00 |
| Margem do prefeito 2020 (pp) | Esquema completo final | -0.11 | -0.12 | -0.03 |
| Margem do prefeito 2020 (pp) | Reforços por hab. (final) | -0.21 | -0.15 | -0.05 |
| Margem do prefeito 2020 (pp) | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.03 | +0.05 | +0.04 |
| Votos do prefeito eleito 2020 (%) | Abandono aproximado | +0.02 | +0.02 | -0.05 |
| Votos do prefeito eleito 2020 (%) | Esquema completo dez/21 (ritmo) | -0.09 | -0.08 | +0.00 |
| Votos do prefeito eleito 2020 (%) | Esquema completo final | -0.07 | -0.07 | -0.01 |
| Votos do prefeito eleito 2020 (%) | Reforços por hab. (final) | -0.11 | -0.07 | +0.01 |
| Votos do prefeito eleito 2020 (%) | Dia em que D1 chegou a 50% (menor = mais rápido) | -0.01 | +0.05 | +0.06 |
| Prefeito reeleito em 2020 (0/1) | Abandono aproximado | +0.04 | -0.01 | +0.04 |
| Prefeito reeleito em 2020 (0/1) | Esquema completo dez/21 (ritmo) | +0.11 | +0.08 | -0.02 |
| Prefeito reeleito em 2020 (0/1) | Esquema completo final | +0.08 | +0.07 | -0.02 |
| Prefeito reeleito em 2020 (0/1) | Reforços por hab. (final) | +0.01 | -0.01 | -0.16 |
| Prefeito reeleito em 2020 (0/1) | Dia em que D1 chegou a 50% (menor = mais rápido) | -0.14 | -0.06 | -0.06 |
| Variação 2018→2022 (pp) [posterior] | Abandono aproximado | +0.13 | +0.32 | +0.24 |
| Variação 2018→2022 (pp) [posterior] | Esquema completo dez/21 (ritmo) | -0.12 | -0.17 | -0.18 |
| Variação 2018→2022 (pp) [posterior] | Esquema completo final | -0.10 | -0.18 | -0.22 |
| Variação 2018→2022 (pp) [posterior] | Reforços por hab. (final) | -0.32 | -0.34 | -0.28 |
| Variação 2018→2022 (pp) [posterior] | Dia em que D1 chegou a 50% (menor = mais rápido) | +0.19 | +0.21 | +0.16 |

## 3. Referência: outras variáveis contra os desfechos (ρ simples)

| variavel          |   cob_comp_dez21_censo |   cob_comp_fim_censo |   cob_ref_fim_censo |   abandono_fim |   dia_d1_50 |
|:------------------|-----------------------:|---------------------:|--------------------:|---------------:|------------:|
| alfab15           |                  -0.16 |                -0.18 |               -0.26 |           0.06 |       -0.04 |
| dist_fortaleza_km |                  -0.03 |                -0.02 |                0.13 |          -0.05 |        0.03 |
| log_densidade     |                  -0.22 |                -0.18 |               -0.19 |           0.16 |        0.02 |
| log_pop2022       |                  -0.26 |                -0.24 |               -0.34 |          -0.02 |        0.16 |
| razao_pop22_21    |                  -0.3  |                -0.28 |               -0.22 |           0.07 |       -0.12 |
| renda_mediana_pc  |                   0.01 |                -0.03 |               -0.07 |          -0.12 |       -0.28 |

Correlação do voto em Bolsonaro 2018 com os controles: log_pop2022 +0.51, log_densidade +0.54, alfab15 +0.59, renda_mediana_pc +0.31, razao_pop22_21 +0.33, dist_fortaleza_km -0.51, idhm +0.46

## 4. Medianas por terço de voto em Bolsonaro 2018

| terco_b18   |   n |   faixa_min |   faixa_max |   cob_comp_dez21_censo |   cob_comp_fim_censo |   cob_ref_fim_censo |   abandono_fim |   dia_d1_50 |
|:------------|----:|------------:|------------:|-----------------------:|---------------------:|--------------------:|---------------:|------------:|
| T1 (menor)  |  62 |       8.545 |      14.914 |                  0.711 |                0.888 |               1.097 |          0.093 |       207.5 |
| T2          |  61 |      14.964 |      21.649 |                  0.715 |                0.881 |               1.076 |          0.106 |       208   |
| T3 (maior)  |  61 |      21.812 |      44.387 |                  0.668 |                0.829 |               0.899 |          0.105 |       208   |

## 5. Partido do prefeito eleito em 2020 (partidos com ≥ 8 prefeitos)

| prefeito_partido_2020   |   n |   cob_comp_dez21_censo |   cob_comp_fim_censo |   cob_ref_fim_censo |   abandono_fim |   dia_d1_50 |
|:------------------------|----:|-----------------------:|---------------------:|--------------------:|---------------:|------------:|
| PDT                     |  64 |                  0.707 |                0.884 |               1.115 |          0.093 |       207   |
| PSD                     |  26 |                  0.669 |                0.839 |               0.955 |          0.126 |       212   |
| PT                      |  18 |                  0.731 |                0.895 |               1.078 |          0.121 |       203.5 |
| MDB                     |  16 |                  0.636 |                0.813 |               1.085 |          0.099 |       219   |
| PL                      |  13 |                  0.677 |                0.836 |               0.908 |          0.104 |       208   |
| PP                      |   9 |                  0.73  |                0.896 |               0.981 |          0.095 |       208   |
| PSB                     |   8 |                  0.714 |                0.871 |               0.998 |          0.066 |       207.5 |

Kruskal-Wallis entre partidos: Esquema completo dez/21 (ritmo): H=6.1, p=0.414; Esquema completo final: H=7.9, p=0.247; Reforços por hab. (final): H=9.3, p=0.156; Abandono aproximado: H=8.9, p=0.179; Dia em que D1 chegou a 50% (menor = mais rápido): H=14.9, p=0.021

## 6. Regressão em postos padronizados (OLS, HC3)

**Esquema completo final** — R² = 0.12, n = 184

| termo | β | IC 95% | p |
|---|---|---|---|
| pct_bolsonaro_2018 | -0.07 | [-0.24, +0.11] | 0.462 |
| log_pop2022 | -0.15 | [-0.32, +0.03] | 0.096 |
| log_densidade | -0.03 | [-0.24, +0.18] | 0.758 |
| alfab15 | -0.03 | [-0.26, +0.20] | 0.805 |
| renda_mediana_pc | +0.11 | [-0.05, +0.28] | 0.167 |
| razao_pop22_21 | -0.22 | [-0.38, -0.07] | 0.005 |

**Esquema completo dez/21 (ritmo)** — R² = 0.15, n = 184

| termo | β | IC 95% | p |
|---|---|---|---|
| pct_bolsonaro_2018 | -0.03 | [-0.21, +0.15] | 0.726 |
| log_pop2022 | -0.18 | [-0.35, -0.00] | 0.047 |
| log_densidade | -0.14 | [-0.34, +0.07] | 0.194 |
| alfab15 | +0.05 | [-0.18, +0.28] | 0.684 |
| renda_mediana_pc | +0.15 | [-0.01, +0.31] | 0.059 |
| razao_pop22_21 | -0.25 | [-0.40, -0.09] | 0.002 |

**Dia em que D1 chegou a 50% (menor = mais rápido)** — R² = 0.17, n = 184

| termo | β | IC 95% | p |
|---|---|---|---|
| pct_bolsonaro_2018 | +0.08 | [-0.11, +0.27] | 0.412 |
| log_pop2022 | +0.26 | [+0.10, +0.43] | 0.002 |
| log_densidade | +0.04 | [-0.16, +0.23] | 0.719 |
| alfab15 | +0.01 | [-0.22, +0.24] | 0.936 |
| renda_mediana_pc | -0.36 | [-0.51, -0.21] | 0.000 |
| razao_pop22_21 | -0.16 | [-0.31, -0.01] | 0.037 |
