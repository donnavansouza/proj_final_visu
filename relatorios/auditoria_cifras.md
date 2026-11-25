# Auditoria das cifras do site

Gerado por `pipeline/auditar_cifras.py`. Compara o que o site exibe (JSONs em `json/`) com `relatorios/verificacoes_finais.md`. NOVO = número que só existe no site, calculado na mesma base (pessoas, residência, Censo 2022).

| Onde | Cifra | Site | Verificações | Status |
|---|---|---|---|---|
| Cap. 3 | Municípios > 100% — registros ÷ Censo (estado b) | 60 | 60 | IGUAL |
| Cap. 3 | Municípios > 100% — pessoas ÷ Censo (estado c) | 41 | 41 | IGUAL |
| Cap. 3 | Acima de 100% com os dois denominadores | 14 | 14 | IGUAL |
| Cap. 3 | Municípios > 100% — registros ÷ estimativa 2021 (estado a) | 37 | — | NOVO |
| Cap. 3 | Excesso de pessoas acima da população | 49,473 | 49,473 | IGUAL |
| Cap. 3 | Excesso como % da população | 0.56% | 0.56% | IGUAL |
| Cap. 3 | Itaitinga — 1ª dose, pessoas ÷ Censo | 66.7% | 66.7% | IGUAL |
| Cap. 3 | Fortaleza — 1ª dose, pessoas ÷ Censo | 90.9% | 90.9% | IGUAL |
| Cap. 2 | Fortaleza — esquema completo (pessoas) | 83.3% | 83.3% | IGUAL |
| Cap. 2 | Fortaleza — abandono individual | 8.4% | 8.4% | IGUAL |
| Cap. 4 | Decomposição: parte da 1ª dose | 59% | 59% | IGUAL |
| Cap. 4 | Decomposição: parte do abandono | 41% | 41% | IGUAL |
| Cap. 4 | Perfil 'os dois problemas' | 7 | 7 | IGUAL |
| Cap. 4 | Perfil 'só começaram atrás' | 5 | 5 | IGUAL |
| Cap. 4 | Perfil 'só não voltaram' | 1 | 1 | IGUAL |
| Cap. 4 | Mediana 1ª dose (pessoas) — os 13 | 74.7% | 74.7% | IGUAL |
| Cap. 4 | Mediana 1ª dose (pessoas) — demais | 92.3% | 92.3% | IGUAL |
| Cap. 4 | Mediana abandono — os 13 | 24.9% | 24.9% | IGUAL |
| Cap. 4 | Mediana abandono — demais | 14.0% | 14.0% | IGUAL |
| Cap. 4 | I de Moran — esquema completo (pessoas) | -0.021 | -0.021 | IGUAL |
| Cap. 4 | I de Moran — voto em Bolsonaro 2018 | +0.533 | +0.533 | IGUAL |
| Cap. 4 | I de Moran — renda mediana | +0.474 | +0.474 | IGUAL |
| Cap. 4 | Nova Olinda — abandono individual | 41.9% | 41.9% | IGUAL |
| Cap. 4 | Aurora — abandono individual | 36.9% | 36.9% | IGUAL |
| Cap. 1 | Doses aplicadas a residentes do CE | 24,403,625 | — | NOVO |
| Cap. 1 | Correlação de postos dez/21 × final | 0.96 | — | NOVO |
| Cap. 1 | Largura da faixa P10–P90 em dez/21 (pontos) | 26% | — | NOVO |
| Cap. 2 | Rede de saúde: ρ parcial (porte e erro de pop.) | +0.13 | — | NOVO |
| Cap. 5 | Reforço: razão entre o décimo de cima e o de baixo | 2.03 | — | NOVO |
| Cap. 5 | R² máximo das variáveis medidas | 23% | — | NOVO |
| Cap. 7 | Nova Olinda — esquema completo (pessoas) | 40.1% | — | NOVO |

**Resumo:** 23 iguais, 0 diferentes, 8 novos.

## Diferenças conhecidas em relação ao roteiro original (não às verificações)

- Doses: o roteiro dizia 24,7 milhões (base `processed_CE`); o site usa os microdados, doses a residentes do CE no mesmo período.
- Correlação dez/21 × final: o roteiro dizia 0,92 (doses); com pessoas é a do quadro acima.
- Contador do capítulo 3: o roteiro dizia 60 → 41 → 14; o estado (a) tem o valor do quadro, e o 14 virou um passo próprio (os que seguem acima de 100% com qualquer denominador).
- R² máximo: o roteiro dizia ~20%; o valor calculado está no quadro.
- Os 13 seguem o critério das verificações (registros ÷ Censo); contando pessoas, 39 municípios ficam abaixo de 70% (nota no próprio capítulo).
