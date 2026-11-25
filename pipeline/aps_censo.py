"""Indicadores de atenção primária (CNES) e do Censo 2022 (SIDRA) por município do CE.

Lê dados/brutos/cnes/ e dados/brutos/ibge/ (gerados por pipeline/coleta_ibge_cnes.py) e dados/processados/municipal.csv (populações e ibge6).
Grava dados/processados/aps_censo_municipal.csv e relatorios/aps_censo_validacao.md.

Critérios (documentar no texto):
- UBS = TP_UNID 01 (Posto de Saúde) + 02 (Centro de Saúde/Unidade Básica), CNES de dezembro.
- Equipes ativas na competência: DT_ATIVA <= competência e (DT_DESAT = 900001 ou DT_DESAT > competência).
  eSF = TIPO_EQP 70; eAP = TIPO_EQP 72; eSB = TIPO_EQP 71.
- Cobertura APS estimada = min(1, (eSF × 3.450 + eAP × 1.725) / pop2022). Inspirada no indicador
  histórico do e-Gestor (3.450 pessoas por eSF); eAP contada como meia equipe. Aproximação.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def cnes(sc: Path, comp: str, pop: pd.Series, ibge6: pd.Series, log: list) -> pd.DataFrame:
    st = pd.read_csv(sc / f"cnes_STCE{comp}.csv", dtype=str, usecols=["CODUFMUN", "TP_UNID"])
    ep = pd.read_csv(sc / f"cnes_EPCE{comp}.csv", dtype=str,
                     usecols=["CODUFMUN", "TIPO_EQP", "DT_ATIVA", "DT_DESAT"])
    c = "20" + comp
    ativa = (ep.DT_ATIVA <= c) & ((ep.DT_DESAT == "900001") | (ep.DT_DESAT > c))
    ep = ep[ativa]
    ubs = st[st.TP_UNID.isin(["01", "02"])].groupby("CODUFMUN").size()
    eq = ep.pivot_table(index="CODUFMUN", columns="TIPO_EQP", aggfunc="size", fill_value=0)
    a = str(comp[:2])
    d = pd.DataFrame(index=ibge6.index)
    m = ibge6.map
    d[f"ubs_{a}"] = ibge6.map(ubs).fillna(0)
    d[f"esf_{a}"] = ibge6.map(eq.get("70", pd.Series(dtype=int))).fillna(0)
    d[f"eap_{a}"] = ibge6.map(eq.get("72", pd.Series(dtype=int))).fillna(0)
    d[f"esb_{a}"] = ibge6.map(eq.get("71", pd.Series(dtype=int))).fillna(0)
    d[f"ubs_10mil_{a}"] = 1e4 * d[f"ubs_{a}"] / pop
    d[f"esf_10mil_{a}"] = 1e4 * d[f"esf_{a}"] / pop
    d[f"cob_aps_est_{a}"] = np.minimum(1, (d[f"esf_{a}"] * 3450 + d[f"eap_{a}"] * 1725) / pop)
    d[f"cob_aps_est_sem_teto_{a}"] = (d[f"esf_{a}"] * 3450 + d[f"eap_{a}"] * 1725) / pop
    log.append(f"- CNES {c}: {len(st)} estabelecimentos, UBS={int(d[f'ubs_{a}'].sum())}; equipes ativas "
               f"{len(ep)} de {ativa.size}; eSF={int(d[f'esf_{a}'].sum())}, eAP={int(d[f'eap_{a}'].sum())}; "
               f"municípios sem eSF: {(d[f'esf_{a}'] == 0).sum()}; cobertura estimada ≥100%: "
               f"{(d[f'cob_aps_est_sem_teto_{a}'] >= 1).sum()} municípios")
    return d


def sidra(sc: Path, tab: str) -> pd.DataFrame:
    d = pd.read_csv(sc / f"sidra_{tab}.csv", dtype=str)
    d["v"] = pd.to_numeric(d.valor.replace({"-": "0"}), errors="coerce")  # "-" = zero absoluto no IBGE
    return d


def censo(sc: Path, log: list) -> pd.DataFrame:
    out = {}
    r = sidra(sc, "10295")
    r = r[r.unidade == "Reais"]
    out["renda_media_pc"] = r[r.variavel.str.contains("médio")].set_index("ibge").v
    out["renda_mediana_pc"] = r[r.variavel.str.contains("mediano")].set_index("ibge").v

    def pct(tab, cat_col, cat, unidade="Percentual"):
        x = sidra(sc, tab)
        x = x[(x.unidade == unidade) & (x[cat_col] == cat)]
        return x.set_index("ibge").v

    i = "cat_Nível de instrução"
    out["pct_superior_18"] = pct("10061", i, "Superior completo")
    out["pct_sem_fund_18"] = pct("10061", i, "Sem instrução e fundamental incompleto")
    rel = "cat_Religião"
    out["pct_evangelicos"] = pct("9537", rel, "Evangélicas")
    out["pct_catolicos"] = pct("9537", rel, "Católica Apostólica Romana")
    out["pct_sem_religiao"] = pct("9537", rel, "Sem religião")
    out["pct_sem_internet"] = pct("9942", "cat_Existência de conexão domiciliar à Internet", "Não")
    out["pct_rural"] = pct("9923", "cat_Situação do domicílio", "Rural")
    d = pd.DataFrame(out)
    d.index = d.index.astype(str)
    faltam = ", ".join(f"{k}={v}" for k, v in d.isna().sum().items() if v) or "nenhum"
    log.append(f"- Censo 2022: {len(d)} municípios; faltantes por coluna: {faltam}")
    soma_rel = (d.pct_evangelicos + d.pct_catolicos + d.pct_sem_religiao)
    log.append(f"- Conferência: católicos+evangélicos+sem religião entre {soma_rel.min():.1f}% e {soma_rel.max():.1f}%")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    cnes_dir, ibge_dir = raiz / "dados/brutos/cnes", raiz / "dados/brutos/ibge"
    m = pd.read_csv(raiz / "dados/processados/municipal.csv", dtype={"ibge": str, "ibge6": str}).set_index("ibge")
    log = ["# Validação — aps_censo_municipal.csv", ""]
    d = cnes(cnes_dir, "2012", m.pop2022, m.ibge6, log).join(cnes(cnes_dir, "2112", m.pop2022, m.ibge6, log))
    d = d.join(censo(ibge_dir, log))
    d["var_esf_20_21"] = d.esf_21 - d.esf_20
    assert len(d) == 184 and d.index.is_unique
    log.append(f"- Linhas: {len(d)}; colunas com NA: {d.columns[d.isna().any()].tolist()}")
    d.index.name = "ibge"
    d.reset_index().to_csv(raiz / "dados/processados/aps_censo_municipal.csv", index=False, float_format="%.6g")
    (raiz / "relatorios/aps_censo_validacao.md").write_text("\n".join(log) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
