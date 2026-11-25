"""Quatro verificações finais antes da visualização. Sem bases novas.

Lê dados/processados/municipal.csv, dados/processados/base_analise.csv e dados/processados/microdados_municipal.csv.
Grava relatorios/verificacoes_finais.md.

1. Os municípios que ficaram para trás começaram atrás (1ª dose) ou só não voltaram (abandono)?
2. Coberturas > 100% por residência: duplicidade, local de aplicação ou denominador?
3. Itaitinga e Região Metropolitana de Fortaleza: cobertura baixa real ou efeito da população do Censo?
4. Há manchas regionais? I de Moran global (pesos de contiguidade padronizados por linha,
   999 permutações) e LISA local.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# RMF: Lei Complementar Estadual 180/2018 (19 municípios)
RMF = ["Aquiraz", "Cascavel", "Caucaia", "Chorozinho", "Eusébio", "Fortaleza", "Guaiúba", "Horizonte",
       "Itaitinga", "Maracanaú", "Maranguape", "Pacajus", "Pacatuba", "Paracuru", "Paraipaba",
       "Pindoretama", "São Gonçalo do Amarante", "São Luís do Curu", "Trairi"]
PERM = 999
rng = np.random.default_rng(2026)


def carregar(raiz: Path) -> pd.DataFrame:
    b = pd.read_csv(raiz / "dados/processados/base_analise.csv", dtype={"ibge": str})
    u = pd.read_csv(raiz / "dados/processados/microdados_municipal.csv", dtype={"ibge": str})
    u["cob_pessoas_d1"] = (u.pessoas_d1 + u.du_res) / u.pop2022
    u["cob_pessoas_comp"] = (u.com_d2 + u.du_res) / u.pop2022
    u["doses_d1_por_pessoa"] = u.d1_res / u.pessoas_d1
    cols = ["ibge", "cob_pessoas_d1", "cob_pessoas_comp", "abandono_individual", "doses_d1_por_pessoa",
            "cob_d1_res", "pct_doses_residentes_no_proprio_mun", "pessoas_d1", "du_res", "com_d2"]
    d = b.merge(u[cols], on="ibge", validate="1:1")
    assert len(d) == 184
    for t in ("jun21", "dez21", "dez22", "fim"):
        d[f"cob_d1_{t}_censo"] = d[f"d1_{t}"] / d.pop2022
    d["baixo"] = d.cob_comp_fim_censo < 0.70
    d["rmf"] = d.municipio.isin(RMF)
    assert d.rmf.sum() == len(RMF), sorted(set(RMF) - set(d.municipio))
    return d.set_index("ibge")


def v1_comecaram_atras(d, L):
    L += ["## 1. Começaram atrás ou não voltaram?", "",
          "Contagens por residência (o processed_CE já é por residência; ver verificação 2). "
          "Medianas por grupo; p = Mann-Whitney.", "",
          "| Indicador | < 70% (n=13) | demais (n=171) | p |", "|---|---|---|---|"]
    for c, nome in [("cob_d1_jun21_censo", "1ª dose até jun/21 (doses/Censo)"),
                    ("cob_d1_dez21_censo", "1ª dose até dez/21"),
                    ("cob_d1_fim_censo", "1ª dose final (doses)"),
                    ("cob_pessoas_d1", "1ª dose final (pessoas)"),
                    ("dia_d1_50", "Dia em que a 1ª dose chegou a 50% (pop. 2021)"),
                    ("abandono_individual", "Abandono individual"),
                    ("cob_pessoas_comp", "Esquema completo (pessoas)")]:
            a, o = d[d.baixo][c], d[~d.baixo][c]
            L.append(f"| {nome} | {a.median():.3f} | {o.median():.3f} | {stats.mannwhitneyu(a, o).pvalue:.2g} |")

    # Decomposição: completo ≈ (pessoas com D1) × (1 − abandono). Diferença em log para a mediana
    # dos demais, repartida entre "começou atrás" (D1) e "não voltou" (abandono).
    ref_d1 = d[~d.baixo].cob_pessoas_d1.median()
    ref_ret = 1 - d[~d.baixo].abandono_individual.median()
    x = d[d.baixo].copy()
    x["parte_d1"] = np.log(ref_d1 / x.cob_pessoas_d1)
    x["parte_aband"] = np.log(ref_ret / (1 - x.abandono_individual))
    tot = x.parte_d1 + x.parte_aband
    x["pct_gap_d1"] = 100 * x.parte_d1 / tot
    x["rank_d1"] = d.cob_pessoas_d1.rank(ascending=False).loc[x.index]
    x["rank_aband"] = d.abandono_individual.rank(ascending=False).loc[x.index]
    x["perfil"] = np.where(x.pct_gap_d1 >= 65, "começou atrás",
                           np.where(x.pct_gap_d1 <= 35, "não voltou", "os dois"))
    L += ["", f"Decomposição da distância para a mediana dos demais (1ª dose {ref_d1:.3f}; "
          f"retenção {ref_ret:.3f}), em log. 'começou atrás' = ≥ 65% da distância vem da 1ª dose; "
          "'não voltou' = ≥ 65% vem do abandono.", "",
          "| Município | 1ª dose (pessoas) | posição 1ª dose | abandono | posição abandono | % da distância pela 1ª dose | perfil |",
          "|---|---|---|---|---|---|---|"]
    for _, r in x.sort_values("pct_gap_d1").iterrows():
        L.append(f"| {r.municipio} | {r.cob_pessoas_d1:.1%} | {r.rank_d1:.0f}ª menor | {r.abandono_individual:.1%} | "
                 f"{r.rank_aband:.0f}º maior | {r.pct_gap_d1:.0f}% | {r.perfil} |")
    soma = x[["parte_d1", "parte_aband"]].sum()
    L += ["", f"No conjunto dos 13: {100*soma.parte_d1/soma.sum():.0f}% da distância vem da 1ª dose e "
          f"{100*soma.parte_aband/soma.sum():.0f}% do abandono. Perfis: {x.perfil.value_counts().to_dict()}.", ""]
    return x


def v2_acima_100(d, L):
    acima_doses = d.cob_d1_res > 1
    acima_pess = d.cob_pessoas_d1 > 1
    so_dup = acima_doses & ~acima_pess
    pop21 = (d.pessoas_d1 + d.du_res) / d.pop2021
    acima_pess_21 = pop21 > 1
    acima_ambos = (d.cob_pessoas_d1 > 1) & (pop21 > 1)
    L += ["## 2. Coberturas acima de 100% (1ª dose, por residência)", "",
          f"- Por doses: **{acima_doses.sum()}** municípios > 100% (Censo).",
          f"- Por pessoas distintas: **{acima_pess.sum()}**. Os {so_dup.sum()} que saem eram só duplicidade: "
          + ", ".join(sorted(d[so_dup].municipio)) + ".",
          f"- Por pessoas com a estimativa de 2021 como denominador: {acima_pess_21.sum()}; "
          f"acima de 100% com os dois denominadores: **{acima_ambos.sum()}**.",
          f"- Local de aplicação: a contagem por residência não depende dele (a dose fica no município do "
          f"paciente onde quer que tenha sido aplicada). Mediana de doses de residentes aplicadas no próprio "
          f"município: {d[acima_pess].pct_doses_residentes_no_proprio_mun.median():.1%} nos > 100% contra "
          f"{d[~acima_pess].pct_doses_residentes_no_proprio_mun.median():.1%} nos demais "
          f"(p = {stats.mannwhitneyu(d[acima_pess].pct_doses_residentes_no_proprio_mun, d[~acima_pess].pct_doses_residentes_no_proprio_mun).pvalue:.2g}).",
          f"- Razão Censo/estimativa: mediana {d[acima_pess].razao_pop22_21.median():.3f} nos > 100% (pessoas) contra "
          f"{d[~acima_pess].razao_pop22_21.median():.3f} nos demais "
          f"(p = {stats.mannwhitneyu(d[acima_pess].razao_pop22_21, d[~acima_pess].razao_pop22_21).pvalue:.2g}).",
          f"- Excesso de 1ª dose acima da população (pessoas, Censo), soma nos > 100%: "
          f"{int(((d.pessoas_d1 + d.du_res) - d.pop2022)[acima_pess].sum()):,} pessoas "
          f"({100*((d.pessoas_d1 + d.du_res) - d.pop2022)[acima_pess].sum()/d.pop2022.sum():.2f}% da população do CE).", ""]
    top = d[acima_pess].sort_values("cob_pessoas_d1", ascending=False).head(10)
    L += ["| Município | doses/Censo | pessoas/Censo | pessoas/est. 2021 | registros de D1 por pessoa | Censo/estimativa |",
          "|---|---|---|---|---|---|"]
    for _, r in top.iterrows():
        L.append(f"| {r.municipio} | {r.cob_d1_res:.1%} | {r.cob_pessoas_d1:.1%} | "
                 f"{(r.pessoas_d1 + r.du_res)/r.pop2021:.1%} | {r.doses_d1_por_pessoa:.3f} | {r.razao_pop22_21:.3f} |")
    L.append("")


def v3_rmf(d, L):
    L += ["## 3. Itaitinga e Região Metropolitana de Fortaleza", "",
          "| Grupo / município | Censo/estimativa | completo (doses/est. 2021) | completo (doses/Censo) | completo (pessoas/Censo) | 1ª dose (pessoas/Censo) | abandono individual |",
          "|---|---|---|---|---|---|---|"]

    def linha(nome, s, agregado):
        if agregado:
            comp21 = s.comp_fim.sum() / s.pop2021.sum()
            compc = s.comp_fim.sum() / s.pop2022.sum()
            compp = (s.com_d2 + s.du_res).sum() / s.pop2022.sum()
            d1p = (s.pessoas_d1 + s.du_res).sum() / s.pop2022.sum()
            ab = 1 - s.com_d2.sum() / s.pessoas_d1.sum()
            raz = s.pop2022.sum() / s.pop2021.sum()
        else:
            r = s.iloc[0]
            comp21, compc, compp = r.comp_fim / r.pop2021, r.cob_comp_fim_censo, r.cob_pessoas_comp
            d1p, ab, raz = r.cob_pessoas_d1, r.abandono_individual, r.razao_pop22_21
        L.append(f"| {nome} | {raz:.3f} | {comp21:.1%} | {compc:.1%} | {compp:.1%} | {d1p:.1%} | {ab:.1%} |")

    linha("RMF (19, agregado)", d[d.rmf], True)
    linha("RMF sem Fortaleza", d[d.rmf & (d.municipio != "Fortaleza")], True)
    linha("Interior (165, agregado)", d[~d.rmf], True)
    L.append("| | | | | | | |")
    for m in d[d.rmf].sort_values("cob_comp_fim_censo").municipio:
        linha(m, d[d.municipio == m], False)
    a, o = d[d.rmf].cob_pessoas_comp, d[~d.rmf].cob_pessoas_comp
    L += ["", f"Mediana do esquema completo (pessoas/Censo): RMF {a.median():.1%} × interior {o.median():.1%} "
          f"(Mann-Whitney p = {stats.mannwhitneyu(a, o).pvalue:.2g}). Municípios da RMF entre os 13 abaixo de 70%: "
          + ", ".join(sorted(d[d.rmf & d.baixo].municipio)) + ".", ""]


def moran(y, W, perm=PERM):
    z = y - y.mean()
    i_obs = (len(y) / W.sum()) * (z @ W @ z) / (z @ z)
    sims = np.array([(len(y) / W.sum()) * (zp @ W @ zp) / (zp @ zp)
                     for zp in (rng.permutation(z) for _ in range(perm))])
    p = (1 + (np.abs(sims - sims.mean()) >= abs(i_obs - sims.mean())).sum()) / (perm + 1)
    return i_obs, -1 / (len(y) - 1), p


def lisa(y, W, perm=PERM):
    z = (y - y.mean()) / y.std()
    lag = W @ z
    ii = z * lag
    n, out = len(y), []
    for i in range(n):
        viz = W[i] > 0
        k = viz.sum()
        outros = np.delete(z, i)
        sims = np.array([z[i] * rng.choice(outros, k, replace=False).mean() for _ in range(perm)])
        p = (1 + (np.abs(sims) >= abs(ii[i])).sum()) / (perm + 1)
        q = ("alto-alto" if z[i] > 0 and lag[i] > 0 else "baixo-baixo" if z[i] < 0 and lag[i] < 0
             else "alto-baixo" if z[i] > 0 else "baixo-alto")
        out.append((p, q))
    return out


def v4_moran(d, L):
    ids = list(d.index)
    pos = {k: i for i, k in enumerate(ids)}
    A = np.zeros((len(ids), len(ids)))
    for k, viz in d.vizinhos.items():
        for j in str(viz).split(";"):
            if j in pos:
                A[pos[k], pos[j]] = 1
    W = A / A.sum(axis=1, keepdims=True)
    L += ["## 4. Manchas regionais: I de Moran", "",
          f"Pesos: contiguidade (lista `vizinhos`), padronizados por linha. {PERM} permutações. "
          "I esperado sem autocorrelação ≈ −0,005. LISA: p < 0,05 sem correção para múltiplos testes "
          "(com 184 testes, ~9 falsos positivos são esperados ao acaso).", "",
          "| Indicador | I de Moran | p | LISA alto-alto | LISA baixo-baixo | municípios baixo-baixo |",
          "|---|---|---|---|---|---|"]
    res = {}
    for c, nome in [("cob_comp_fim_censo", "Esquema completo final (doses/Censo)"),
                    ("cob_pessoas_comp", "Esquema completo final (pessoas/Censo)"),
                    ("cob_comp_dez21_censo", "Esquema completo dez/21"),
                    ("cob_pessoas_d1", "1ª dose (pessoas)"),
                    ("abandono_individual", "Abandono individual"),
                    ("cob_ref_fim_censo", "Reforços por hab."),
                    ("dia_d1_50", "Dia em que a 1ª dose chegou a 50%"),
                    ("pct_bolsonaro_2018", "Referência: voto Bolsonaro 2018"),
                    ("renda_mediana_pc", "Referência: renda mediana 2022")]:
        y = d[c].to_numpy(float)
        i_obs, ei, p = moran(y, W)
        loc = lisa(y, W)
        hh = [ids[i] for i, (pl, q) in enumerate(loc) if pl < 0.05 and q == "alto-alto"]
        ll = [ids[i] for i, (pl, q) in enumerate(loc) if pl < 0.05 and q == "baixo-baixo"]
        res[c] = (i_obs, p)
        L.append(f"| {nome} | {i_obs:+.3f} | {p:.3f} | {len(hh)} | {len(ll)} | "
                 f"{', '.join(d.loc[ll, 'municipio']) or '—'} |")
    L.append("")
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    d = carregar(raiz)
    L = ["# Verificações finais", "",
         "13 municípios com esquema completo < 70% (doses/Censo): " + ", ".join(sorted(d[d.baixo].municipio)) + ".", ""]
    v1_comecaram_atras(d, L)
    v2_acima_100(d, L)
    v3_rmf(d, L)
    v4_moran(d, L)
    (raiz / "relatorios/verificacoes_finais.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
