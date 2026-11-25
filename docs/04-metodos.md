# 4. Métodos estatísticos

> Cada método aparece com: **a pergunta** que ele responde, **a intuição**, **a conta**, **onde foi usado**
> e **o cuidado**. O código está em `pipeline/analise_politica.py`, `pipeline/analise_eixos.py` e
> `pipeline/verificacoes_finais.py`.

## 4.1 Percentis e a faixa P10–P90

**Pergunta:** quão diferentes eram os municípios num dado momento?

**Intuição:** ordene os 184 municípios pela cobertura. O P10 é o valor abaixo do qual ficam 10% deles;
o P90, abaixo do qual ficam 90%. A faixa entre os dois contém os 80% "do meio" e ignora extremos (que,
aqui, muitas vezes são erro de medida).

**No projeto (cap. 1):** a largura P90 − P10 do esquema completo foi de 8 pontos (jun/21) para 26
(dez/21) e 28 (fim). A desigualdade se formou em 2021 e depois parou de crescer.

**Por que não o desvio-padrão?** É sensível a valores extremos — e temos municípios com 112%.

## 4.2 Correlação de postos de Spearman (ρ)

**Pergunta:** quando X sobe, Y tende a subir (ou cair)?

**Intuição:** troque cada valor pela sua **posição** (1º, 2º, …, 184º) e calcule a correlação de
Pearson entre as posições. Vai de −1 (ordem inversa perfeita) a +1 (mesma ordem); 0 = sem relação monótona.

```
ρ = correlação de Pearson entre posto(X) e posto(Y)
```

**Por que postos e não os valores?** Robustez: um município com 112% de cobertura ou R$ 1.212 de renda
(Fortaleza) não domina a conta. E capta relações monótonas que não são retas.

**No projeto:** correlação da posição dos municípios em dez/21 com a final = **0,96** (a ordem quase não
mudou). Renda × esquema completo = −0,12.

**Cuidado:** correlação não é causa; e ρ mede só relações monótonas (uma relação em "U" pode dar ρ ≈ 0).

## 4.3 Correlação parcial (controlar por terceiras variáveis)

**Pergunta:** a relação entre X e Y continua quando descontamos Z?

**Intuição:** o voto em Bolsonaro e a cobertura se correlacionam (ρ = −0,19). Mas os dois dependem do
**porte**: municípios maiores votaram mais em Bolsonaro *e* vacinaram menos por habitante. A correlação
parcial pergunta: entre municípios **de mesmo porte**, ainda há relação?

**A conta (em postos):**
1. Converta X, Y e os controles em postos.
2. Regrida posto(X) nos controles e guarde o **resíduo** (o que sobra de X depois de explicado pelos controles).
3. Faça o mesmo com Y.
4. A correlação entre os dois resíduos é o ρ parcial.

**No projeto:** voto × cobertura cai de −0,19 para **−0,01** controlando porte, densidade, alfabetização
e renda. É o resultado central do capítulo 2: a associação aparente vinha do perfil urbano. Controles
padrão do site: log da população e razão Censo/estimativa (erro de população).

**Cuidado:** controlar demais pode apagar efeitos reais (se o controle está no caminho causal). Por isso
o site mostra sempre o ρ simples **e** o parcial.

## 4.4 Muitos testes ao mesmo tempo: FDR (Benjamini–Hochberg)

**Problema:** testando 6 variáveis × 5 desfechos × 3 amostras = 90 correlações, algumas darão
p < 0,05 **por acaso** (esperam-se ~5 em 100 mesmo sem nenhum efeito real).

**Solução:** o procedimento de Benjamini e Hochberg (1995) ajusta os valores-p para controlar a
**taxa de falsas descobertas** (FDR): entre os resultados declarados significativos, no máximo ~5% são
falsos. O valor ajustado chama-se **q**.

**Como funciona:** ordene os p do menor ao maior; o i-ésimo vira `q = p × m / i` (m = total de testes),
corrigido para nunca diminuir.

**No projeto:** a variação do voto × reforço sobreviveu (q = 0,001); quase todo o resto não.

## 4.5 Regressão em postos com erros robustos

**Pergunta:** juntando um representante de cada eixo (porte, erro de população, renda, rural, religião,
equipes, voto), quanto da variação entre municípios eles explicam juntos? E qual pesa mais?

**A conta:** regressão linear (MQO) com todas as variáveis convertidas em postos e padronizadas
(média 0, desvio 1). Os coeficientes (β) ficam comparáveis entre si. Erros-padrão **HC3**, que não
supõem variância constante dos resíduos.

**R²:** fração da variação explicada. No projeto, **no máximo 23%** (para o ritmo da 1ª dose); 15% para
o esquema completo. Ou seja: ~80% das diferenças entre municípios **não** são explicadas pelo que medimos.

**VIF (fator de inflação da variância):** mede se uma variável explicativa é quase cópia das outras.
Todos ficaram entre 1,3 e 2,0 (sem colinearidade preocupante; o alerta usual começa em 5 ou 10).

## 4.6 Mann-Whitney (comparar dois grupos)

**Pergunta:** os 13 municípios atrasados diferem dos outros 171 em X?

**Intuição:** versão em postos do teste t. Junta os dois grupos, ordena e verifica se um grupo concentra
as posições altas (ou baixas) mais do que o acaso explicaria. Não supõe distribuição normal.

**No projeto (verificações):** abandono individual 24,9% nos 13 contra 14,0% nos demais (p ≈ 0,000003);
1ª dose 74,7% contra 92,3%. Já renda, voto, religião e equipes **não** diferem.

## 4.7 Decomposição: "começaram atrás" ou "não voltaram"?

**Pergunta:** a cobertura completa baixa vem de pouca 1ª dose ou de muito abandono?

**Intuição:** completo ≈ (1ª dose) × (1 − abandono). Com logaritmos, um produto vira soma:

```
log(completo_ref / completo_mun) = log(d1_ref / d1_mun) + log(retenção_ref / retenção_mun)
                                    └── parte da 1ª dose ─┘   └──── parte do abandono ───┘
```

A referência é a mediana dos outros 171 municípios (1ª dose 92,3%; retenção 86,0%).

**No projeto:** somando os 13, **59% da distância vem da 1ª dose e 41% do abandono**. Cada município
recebe um perfil: ≥ 65% de uma das partes → "começou atrás" ou "não voltou"; senão, "os dois problemas".
Resultado: 7 com os dois, 5 só começaram atrás, 1 (Aurora) só não voltou.

**Cuidado:** o corte de 65% é uma convenção nossa; mudar para 60% ou 70% muda alguns perfis.

## 4.8 Autocorrelação espacial: I de Moran

**Pergunta:** municípios vizinhos se parecem mais do que municípios quaisquer? Ou: o mapa forma **manchas**?

**Intuição:** compare cada município com a **média dos vizinhos**. Se valores altos ficam perto de
altos e baixos perto de baixos, o I é positivo (manchas). Perto de 0: o vizinho não diz nada sobre você
(mapa "salpicado"). Negativo: vizinhos tendem a ser opostos (tabuleiro de xadrez).

```
I = (n / ΣW) × Σᵢ Σⱼ wᵢⱼ (xᵢ − x̄)(xⱼ − x̄) / Σᵢ (xᵢ − x̄)²
```

- `wᵢⱼ` = 1 se *i* e *j* fazem fronteira (padronizado por linha: cada município soma 1).
- Sem autocorrelação, o valor esperado é −1/(n−1) ≈ −0,005.
- **Significância por permutação:** embaralhamos os valores entre os municípios 999 vezes e vemos
  quantas vezes o I embaralhado é tão extremo quanto o real.

**No projeto:** esquema completo **−0,02** (p = 0,72: sem manchas); voto em Bolsonaro **+0,53** e renda
**+0,47** (p = 0,001: manchas fortes). É a base da frase "a vacinação não forma manchas".

**LISA (I de Moran local, Anselin 1995):** a mesma ideia, município por município — indica focos
"alto-alto" e "baixo-baixo". Com 184 testes, ~9 falsos positivos são esperados ao acaso; por isso não
destacamos focos locais no site.

## 4.9 Resumo: o que cada método disse

| Pergunta | Método | Resposta |
|---|---|---|
| A desigualdade cresceu? | Percentis | Abriu até dez/21 e parou |
| A ordem mudou depois? | Spearman | Não (0,96) |
| Os suspeitos explicam? | Spearman simples e parcial | Associações somem com controles |
| Algo sobra? | FDR | Só o reforço × variação do voto |
| Quanto se explica? | Regressão em postos | No máximo 23% |
| Os atrasados são diferentes? | Mann-Whitney | Só em 1ª dose e abandono |
| Por quê atrasaram? | Decomposição em log | 59% 1ª dose, 41% abandono |
| Há regiões atrasadas? | I de Moran | Não; voto e renda sim |

## Perguntas de revisão

1. Por que Spearman e não Pearson neste projeto?
2. Explique com suas palavras por que a correlação voto × cobertura "some" com controles.
3. Se você fizer 100 testes sem nenhum efeito real, quantos darão p < 0,05? O que o FDR faz com isso?
4. O R² máximo foi 23%. O que isso diz sobre os outros 77%?
5. Por que a decomposição usa logaritmos?
6. O que significa um I de Moran de −0,02? E de +0,53?
7. Por que o teste do I de Moran é feito por permutação?
