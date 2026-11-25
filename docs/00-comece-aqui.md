# 0. Comece aqui: o essencial em 3 dias

> O projeto é grande, mas **ninguém precisa dominar tudo**. Uma banca pergunta sobre a história, as
> decisões e o porquê dos gráficos, quase nunca sobre como uma função foi escrita. Este guia separa
> o que vocês precisam saber explicar do que podem tratar como caixa-preta ("existe, funciona, está
> documentado"). Os documentos 01 a 06 ficam para aprofundar.

## O que precisa dominar × o que pode ser caixa-preta

| Precisa saber explicar | Basta saber que existe |
|---|---|
| A pergunta e a resposta, em 1 minuto | Como o leitor de `.dbc` do DATASUS funciona |
| As 3 correções da medida (denominador, pessoas, residência) | Os detalhes de Spearman parcial, HC3, BH/FDR |
| Por que cada "suspeito" foi descartado | Como o LISA (Moran local) é calculado |
| O que significam ρ, "com controles" e I de Moran, em palavras | O código do Scrollama e das transições do D3 |
| Por que cada gráfico é o tipo de gráfico que é | O pipeline de testes (`testes/`) |
| As cores: por que tons de azul no mapa, terracota × azul nas linhas | Como os JSONs são gerados (`pipeline/preparar_site.py`) |
| Os limites (falácia ecológica, associação ≠ causa) | Os hashes do inventário (`docs/06`) |

## A história em 6 frases (decore esta)

1. **Pergunta:** quem ficou para trás na vacinação contra a Covid-19 entre os 184 municípios do Ceará, e por quê?
2. **Os suspeitos de sempre** (renda, interior, política, rede de saúde, hábito vacinal) foram testados e **não explicam** a desigualdade.
3. **A reviravolta:** parte da desigualdade estava na **medida**: população desatualizada, a mesma pessoa contada duas vezes e um abandono que chegava a dar negativo.
4. **Corrigida a medida** (Censo 2022, pessoas e não registros, município de residência), os municípios "acima de 100%" caem de 60 para 41, e só 14 ficam acima com qualquer denominador.
5. **Quem ficou para trás de verdade:** 13 municípios abaixo de 70% de esquema completo, que **começaram atrás** (1ª dose 75% × 92%) **e não trouxeram as pessoas de volta** (abandono 25% × 14%).
6. **O que fica em aberto:** é algo local (gestão, busca ativa), que nossos dados não medem.

## Os 10 números

| Número | O que é |
|---|---|
| 184 | municípios do Ceará |
| 24,4 milhões | doses aplicadas a residentes (17/01/2021–16/04/2024) |
| 90% / 79% | população com 1ª dose / esquema completo (Censo 2022) |
| 50% → 102% | Catarina, 1ª dose, com a estimativa 2021 × com o Censo 2022 |
| 60 → 41 → 14 | municípios acima de 100%: registros → pessoas → com qualquer denominador |
| 0,96 | correlação entre a posição em dez/21 e a final: a desigualdade congelou cedo |
| −0,19 → −0,01 | correlação voto 2018 × cobertura, sem e com controles de porte |
| 23% | o máximo que todas as variáveis juntas explicam |
| −0,02 | I de Moran da cobertura: o mapa não forma "manchas" (voto: +0,53; renda: +0,47) |
| 13 / 59% | municípios abaixo de 70%; parte da distância que vem da 1ª dose (o resto, 41%, do abandono) |

## Plano de 3 dias

Dividam: **um fica com "dados e análise"**, o outro com **"site e visualização"**. Cada um estuda a
sua metade a fundo e a do outro só no nível da tabela acima.

| Dia | Os dois juntos (1 h) | Dados e análise | Site e visualização |
|---|---|---|---|
| **1. A história** | Leiam o site inteiro, rolando devagar. Um conta a história ao outro em 2 min, sem olhar | [02-dados.md](02-dados.md) §2.3 (decisões) | [01-tecnico.md](01-tecnico.md) §1.1, 1.3 e 1.4 (arquitetura e scrollytelling) |
| **2. O porquê** | Para cada capítulo: "por que este gráfico e não outro?" | [04-metodos.md](04-metodos.md) §4.9 (resumo) e a intuição de §4.2, 4.3, 4.7 e 4.8 | [03-tipos-de-dados.md](03-tipos-de-dados.md) §3.2, 3.4 e 3.6 (atributos, forma do gráfico, cor) |
| **3. Ensaio** | Respondam as perguntas de [05-guia-de-estudo.md](05-guia-de-estudo.md) §5.2 um para o outro | Treinar as perguntas "sobre os dados" | Abrir o Explore e mostrar um município ao vivo |

## Se perguntarem algo que vocês não sabem

Resposta honesta e segura: *"Isso está documentado no repositório. A decisão foi X por causa de Y; o
detalhe da implementação está em `docs/0N`."* Ninguém espera que vocês recitem código.
