"""Eixo político × vacinação: Spearman, Spearman parcial, regressão em postos, partidos.

Junta dados/processados/municipal.csv (gerado por pipeline/base_municipal.py) e dados/processados/tse_municipal.csv por ibge e grava
dados/processados/base_analise.csv, dados/processados/correlacoes_politica.csv e relatorios/analise_politica.md.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DESFECHOS = {
    "cob_comp_dez21_censo": "Esquema completo dez/21 (ritmo)",
    "cob_comp_fim_censo": "Esquema completo final",
    "cob_ref_fim_censo": "Reforços por hab. (final)",
    "abandono_fim": "Abandono aproximado",
    "dia_d1_50": "Dia em que D1 chegou a 50% (menor = mais rápido)",
}
POLITICAS = {
    "pct_bolsonaro_2018": "Bolsonaro 2º t. 2018 (%)",
    "pct_bolsonaro_1t_2018": "Bolsonaro 1º t. 2018 (%)",
    "pct_bolsonaro_2022": "Bolsonaro 2º t. 2022 (%) [posterior]",
    "var_bolsonaro_18_22": "Variação 2018→2022 (pp) [posterior]",
    "prefeito_pct_votos_2020": "Votos do prefeito eleito 2020 (%)",
    "prefeito_margem_2020": "Margem do prefeito 2020 (pp)",
    "prefeito_reeleito_2020": "Prefeito reeleito em 2020 (0/1)",
    "comparecimento_2018": "Comparecimento 2º t. 2018 (%)",
}
CONTROLES = ["log_pop2022", "log_densidade", "alfab15", "renda_mediana_pc"]


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def spearman_parcial(d, x, y, ctrl):
    d = d[[x, y] + ctrl].dropna().rank()
    Z = np.column_stack([np.ones(len(d)), d[ctrl].values])
    res = lambda v: v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    r = np.corrcoef(res(d[x].values), res(d[y].values))[0, 1]
    gl = len(d) - 2 - len(ctrl)
    t = r * np.sqrt(gl / (1 - r ** 2))
    return r, 2 * stats.t.sf(abs(t), gl), len(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    vac = pd.read_csv(raiz / "dados/processados/municipal.csv", dtype={"ibge": str, "ibge6": str})
    # derivadas que o pipeline/base_municipal.py não grava
    vac["cob_comp_dez21_censo"] = vac.comp_dez21 / vac.pop2022
    vac["cob_ref_fim_censo"] = vac.ref_fim / vac.pop2022
    vac["log_pop2022"] = np.log10(vac.pop2022)
    vac["log_densidade"] = np.log10(vac.densidade)
    vac["alerta_censo"] = (vac.cob_d1_fim_censo > 1) | (vac.cob_comp_fim_censo > 1) | (vac.abandono_fim < 0)
    tse = pd.read_csv(raiz / "dados/processados/tse_municipal.csv", dtype={"ibge": str, "cd_tse": str})
    d = vac.merge(tse.drop(columns="municipio"), on="ibge", how="outer", indicator=True)
    assert (d._merge == "both").all() and len(d) == 184
    d = d.drop(columns="_merge")
    aps = pd.read_csv(raiz / "dados/processados/aps_censo_municipal.csv", dtype={"ibge": str})
    d = d.merge(aps, on="ibge", how="left", validate="1:1")
    assert len(d) == 184 and d.renda_mediana_pc.notna().all()
    d["prefeito_reeleito_2020"] = d.prefeito_reeleito_2020.astype(float)
    d.to_csv(raiz / "dados/processados/base_analise.csv", index=False, float_format="%.6g")

    amostras = {"todos": d, "sem_alerta": d[~d.alerta], "sem_alerta_censo": d[~d.alerta_censo]}
    linhas = []
    for am, s in amostras.items():
        for x in POLITICAS:
            for y in DESFECHOS:
                t = s[[x, y]].dropna()
                rho, p = stats.spearmanr(t[x], t[y])
                rp, pp, _ = spearman_parcial(s, x, y, CONTROLES)
                rp2, pp2, _ = spearman_parcial(s, x, y, CONTROLES + ["razao_pop22_21"])
                linhas.append(dict(amostra=am, politica=x, desfecho=y, n=len(t), rho=rho, p=p,
                                   rho_parcial=rp, p_parcial=pp, rho_parcial_pop=rp2, p_parcial_pop=pp2))
    c = pd.DataFrame(linhas)
    for col in ["p", "p_parcial", "p_parcial_pop"]:
        c["q_" + col] = c.groupby("amostra")[col].transform(bh)
    c.to_csv(raiz / "dados/processados/correlacoes_politica.csv", index=False, float_format="%.4f")

    # Referência: controles contra os desfechos (mesma escala de comparação)
    ref = []
    for x in CONTROLES + ["razao_pop22_21", "dist_fortaleza_km"]:
        for y in DESFECHOS:
            t = d[[x, y]].dropna()
            ref.append(dict(variavel=x, desfecho=y, rho=stats.spearmanr(t[x], t[y])[0]))
    ref = pd.DataFrame(ref).pivot(index="variavel", columns="desfecho", values="rho")[list(DESFECHOS)]
    ctrl_bolso = {x: stats.spearmanr(d.pct_bolsonaro_2018, d[x])[0] for x in CONTROLES + ["razao_pop22_21", "dist_fortaleza_km", "idhm"]}

    # Terços de voto em Bolsonaro 2018: medianas dos desfechos
    d["terco_b18"] = pd.qcut(d.pct_bolsonaro_2018, 3, labels=["T1 (menor)", "T2", "T3 (maior)"])
    tercos = d.groupby("terco_b18", observed=True).agg(
        n=("ibge", "size"), faixa_min=("pct_bolsonaro_2018", "min"), faixa_max=("pct_bolsonaro_2018", "max"),
        **{k: (k, "median") for k in DESFECHOS})

    # Partido do prefeito eleito (só partidos com >= 8 prefeitos), Kruskal-Wallis
    e = d[d.prefeito_status_2020 == "eleito"]
    grandes = e.prefeito_partido_2020.value_counts()
    grandes = grandes[grandes >= 8].index
    eg = e[e.prefeito_partido_2020.isin(grandes)]
    kw = {y: stats.kruskal(*[g[y].dropna() for _, g in eg.groupby("prefeito_partido_2020")]) for y in DESFECHOS}
    part = eg.groupby("prefeito_partido_2020").agg(
        n=("ibge", "size"), **{k: (k, "median") for k in DESFECHOS}).sort_values("n", ascending=False)

    # Regressão em postos (OLS, erros HC3) para o desfecho principal
    import statsmodels.api as sm
    regs = {}
    for y in ["cob_comp_fim_censo", "cob_comp_dez21_censo", "dia_d1_50"]:
        cols = ["pct_bolsonaro_2018"] + CONTROLES + ["razao_pop22_21"]
        t = d[[y] + cols].dropna().rank()
        t = (t - t.mean()) / t.std()
        m = sm.OLS(t[y], sm.add_constant(t[cols])).fit(cov_type="HC3")
        regs[y] = m

    # Relatório
    L = ["# Eixo político × vacinação — resultados exploratórios", "",
         f"n = {len(d)} municípios; sem alerta (pop2021) = {(~d.alerta).sum()}; "
         f"sem alerta (Censo) = {(~d.alerta_censo).sum()}.",
         "Controles da correlação parcial: " + ", ".join(CONTROLES) +
         " (renda_mediana_pc = rendimento domiciliar per capita mediano, Censo 2022).", "",
         "## 1. Spearman simples e parcial (todos os municípios)", "",
         "| Variável política | Desfecho | ρ | p | ρ parcial | p parcial | ρ parcial + erro de pop. | q (FDR, parcial+pop) |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in c[c.amostra == "todos"].iterrows():
        L.append(f"| {POLITICAS[r.politica]} | {DESFECHOS[r.desfecho]} | {r.rho:+.2f} | {r.p:.3f} | "
                 f"{r.rho_parcial:+.2f} | {r.p_parcial:.3f} | {r.rho_parcial_pop:+.2f} | {r.q_p_parcial_pop:.3f} |")
    L += ["", "## 2. Estabilidade: ρ simples por amostra", "",
          "| Variável política | Desfecho | todos | sem alerta | sem alerta (Censo) |", "|---|---|---|---|---|"]
    w = c.pivot_table(index=["politica", "desfecho"], columns="amostra", values="rho")
    for (x, y), r in w.iterrows():
        L.append(f"| {POLITICAS[x]} | {DESFECHOS[y]} | {r.todos:+.2f} | {r.sem_alerta:+.2f} | {r.sem_alerta_censo:+.2f} |")
    L += ["", "## 3. Referência: outras variáveis contra os desfechos (ρ simples)", "",
          ref.round(2).to_markdown(), "",
          "Correlação do voto em Bolsonaro 2018 com os controles: " +
          ", ".join(f"{k} {v:+.2f}" for k, v in ctrl_bolso.items()), "",
          "## 4. Medianas por terço de voto em Bolsonaro 2018", "", tercos.round(3).to_markdown(), "",
          "## 5. Partido do prefeito eleito em 2020 (partidos com ≥ 8 prefeitos)", "",
          part.round(3).to_markdown(), "",
          "Kruskal-Wallis entre partidos: " + "; ".join(f"{DESFECHOS[k]}: H={v.statistic:.1f}, p={v.pvalue:.3f}" for k, v in kw.items()),
          "", "## 6. Regressão em postos padronizados (OLS, HC3)", ""]
    for y, m in regs.items():
        L.append(f"**{DESFECHOS[y]}** — R² = {m.rsquared:.2f}, n = {int(m.nobs)}")
        L.append("")
        L.append("| termo | β | IC 95% | p |")
        L.append("|---|---|---|---|")
        ci = m.conf_int()
        for k in m.params.index[1:]:
            L.append(f"| {k} | {m.params[k]:+.2f} | [{ci.loc[k,0]:+.2f}, {ci.loc[k,1]:+.2f}] | {m.pvalues[k]:.3f} |")
        L.append("")
    (raiz / "relatorios/analise_politica.md").write_text("\n".join(L), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
