"""Todos os eixos × vacinação, sobre dados/processados/base_analise.csv (gerada por analise_politica.py).

Grava dados/processados/correlacoes_eixos.csv e relatorios/analise_eixos.md.
- Spearman simples e parcial (controle mínimo: porte e erro do denominador), por amostra.
- FDR (Benjamini-Hochberg) sobre todos os testes da amostra.
- Regressão em postos com um representante por eixo + VIF.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from analise_politica import DESFECHOS, bh, spearman_parcial  # noqa: E402

EIXOS = {
    "Socioeconômico (Censo 2022)": {
        "renda_mediana_pc": "Renda domiciliar per capita mediana (R$)",
        "pct_superior_18": "Superior completo, 18+ (%)",
        "pct_sem_fund_18": "Sem instrução/fund. incompleto, 18+ (%)",
        "alfab15": "Alfabetização 15+ (%)",
        "pct_sem_internet": "Moradores sem internet (%)",
        "pct_rural": "População rural (%)",
    },
    "Religião (Censo 2022)": {
        "pct_evangelicos": "Evangélicos (%)",
        "pct_catolicos": "Católicos (%)",
        "pct_sem_religiao": "Sem religião (%)",
    },
    "Atenção primária (CNES)": {
        "esf_10mil_21": "Equipes de Saúde da Família por 10 mil hab. (dez/21)",
        "esf_10mil_20": "Equipes de Saúde da Família por 10 mil hab. (dez/20)",
        "ubs_10mil_21": "UBS por 10 mil hab. (dez/21)",
        "var_esf_20_21": "Variação no nº de eSF 2020→21",
        "cob_aps_est_sem_teto_21": "Capacidade APS estimada / pop. (sem teto)",
    },
    "Histórico sanitário": {
        "mort20_100k": "Mortalidade Covid 2020 por 100 mil",
        "flu_idosos_cob": "Cobertura influenza idosos 2019",
    },
    "Porte e medida": {
        "log_pop2022": "log10 população 2022",
        "log_densidade": "log10 densidade",
        "razao_pop22_21": "Censo 2022 / estimativa 2021",
    },
}
CTRL = ["log_pop2022", "razao_pop22_21"]
MODELO = ["log_pop2022", "razao_pop22_21", "renda_mediana_pc", "pct_rural", "pct_evangelicos",
          "esf_10mil_21", "pct_bolsonaro_2018"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    d = pd.read_csv(raiz / "dados/processados/base_analise.csv", dtype={"ibge": str})
    assert len(d) == 184
    rotulo = {k: v for e in EIXOS.values() for k, v in e.items()}
    eixo_de = {k: e for e, vs in EIXOS.items() for k in vs}
    amostras = {"todos": d, "sem_alerta": d[~d.alerta], "sem_alerta_censo": d[~d.alerta_censo]}

    linhas = []
    for am, s in amostras.items():
        for x in rotulo:
            for y in DESFECHOS:
                t = s[[x, y]].dropna()
                rho, p = stats.spearmanr(t[x], t[y])
                ctrl = [c for c in CTRL if c != x]
                rp, pp, _ = spearman_parcial(s, x, y, ctrl)
                linhas.append(dict(amostra=am, eixo=eixo_de[x], variavel=x, desfecho=y, n=len(t),
                                   rho=rho, p=p, rho_parcial=rp, p_parcial=pp))
    c = pd.DataFrame(linhas)
    for col in ["p", "p_parcial"]:
        c["q_" + col] = c.groupby("amostra")[col].transform(bh)
    c.to_csv(raiz / "dados/processados/correlacoes_eixos.csv", index=False, float_format="%.4f")

    L = ["# Todos os eixos × vacinação — resultados exploratórios", "",
         f"n = 184; sem alerta = {(~d.alerta).sum()}; sem alerta (Censo) = {(~d.alerta_censo).sum()}. "
         "ρ parcial controla porte (log pop. 2022) e erro do denominador (Censo/estimativa). "
         "q = FDR de Benjamini-Hochberg sobre todos os testes da amostra. "
         "Marcados com **negrito**: q parcial < 0,05 em todas as três amostras.", ""]
    w = c.pivot_table(index=["variavel", "desfecho"], columns="amostra",
                      values=["rho", "rho_parcial", "q_p_parcial"])
    for eixo, vs in EIXOS.items():
        L += [f"## {eixo}", "",
              "| Variável | Desfecho | ρ | ρ parcial | ρ parcial sem alerta | ρ parcial sem alerta (Censo) | q parcial (todos) |",
              "|---|---|---|---|---|---|---|"]
        for x in vs:
            for y in DESFECHOS:
                r = w.loc[(x, y)]
                robusto = all(r[("q_p_parcial", a)] < 0.05 for a in amostras)
                b = "**" if robusto else ""
                L.append(f"| {b}{vs[x]}{b} | {DESFECHOS[y]} | {r[('rho', 'todos')]:+.2f} | "
                         f"{r[('rho_parcial', 'todos')]:+.2f} | {r[('rho_parcial', 'sem_alerta')]:+.2f} | "
                         f"{r[('rho_parcial', 'sem_alerta_censo')]:+.2f} | {r[('q_p_parcial', 'todos')]:.3f} |")
        L.append("")

    # Regressão em postos: um representante por eixo
    L += ["## Regressão em postos padronizados (OLS, HC3), um representante por eixo", ""]
    X = d[MODELO].rank()
    X = (X - X.mean()) / X.std()
    vif = {k: 1 / (1 - sm.OLS(X[k], sm.add_constant(X.drop(columns=k))).fit().rsquared) for k in MODELO}
    L.append("VIF: " + ", ".join(f"{k} {v:.1f}" for k, v in vif.items()))
    L.append("")
    for y in ["cob_comp_dez21_censo", "cob_comp_fim_censo", "cob_ref_fim_censo", "abandono_fim", "dia_d1_50"]:
        for nome, s in [("todos", d), ("sem alerta (Censo)", d[~d.alerta_censo])]:
            t = s[[y] + MODELO].dropna().rank()
            t = (t - t.mean()) / t.std()
            m = sm.OLS(t[y], sm.add_constant(t[MODELO])).fit(cov_type="HC3")
            ci = m.conf_int()
            L += [f"**{DESFECHOS[y]}**, {nome} — R² = {m.rsquared:.2f}, n = {int(m.nobs)}", "",
                  "| termo | β | IC 95% | p |", "|---|---|---|---|"]
            for k in MODELO:
                L.append(f"| {k} | {m.params[k]:+.2f} | [{ci.loc[k, 0]:+.2f}, {ci.loc[k, 1]:+.2f}] | {m.pvalues[k]:.3f} |")
            L.append("")

    # Quem ficou para trás: perfil dos 13 municípios < 70% vs. demais (medianas)
    baixo = d.cob_comp_fim_censo < 0.70
    perfil = pd.DataFrame({f"< 70% (n={baixo.sum()})": d[baixo][list(rotulo)].median(),
                           f"demais (n={(~baixo).sum()})": d[~baixo][list(rotulo)].median()})
    perfil["Mann-Whitney p"] = [stats.mannwhitneyu(d[baixo][k].dropna(), d[~baixo][k].dropna()).pvalue for k in rotulo]
    perfil.index = [rotulo[k] for k in perfil.index]
    L += ["## Perfil dos municípios com esquema completo < 70% (Censo) × demais (medianas)", "",
          "Municípios: " + ", ".join(sorted(d[baixo].municipio)), "", perfil.round(3).to_markdown(), ""]
    (raiz / "relatorios/analise_eixos.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
