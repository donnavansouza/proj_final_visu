"""Gera os JSONs enxutos do site (data/) a partir de dados/ e da malha municipal.

Regra: uma base só — microdados, PESSOAS por município de RESIDÊNCIA, Censo 2022 como
denominador. A única exceção é o estado (a) do capítulo 3, que usa a estimativa de 2021
de propósito, para mostrar o erro.

Uso:  python pipeline/preparar_site.py --raiz .
Entradas: dados/processados/municipal.csv (só nomes e populações), dados/processados/microdados_municipal.csv,
          dados/processados/microdados_serie_semanal.csv, dados/processados/microdados_doses_diarias.csv,
          dados/brutos/referencia/geojs-23-mun.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# RMF: Lei Complementar Estadual 180/2018 (mesma lista de verificacoes_finais.py)
RMF = ["Aquiraz", "Cascavel", "Caucaia", "Chorozinho", "Eusébio", "Fortaleza", "Guaiúba", "Horizonte",
       "Itaitinga", "Maracanaú", "Maranguape", "Pacajus", "Pacatuba", "Paracuru", "Paraipaba",
       "Pindoretama", "São Gonçalo do Amarante", "São Luís do Curu", "Trairi"]
SENSIVEL_DENOMINADOR = ["2306256"]  # Itaitinga (verificacoes_finais.md, seção 3)
EXCESSO_VERIFICACOES = 49_473        # verificacoes_finais.md, seção 2 (conferido abaixo)


def r(x, n=6):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def salvar(obj, path: Path):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {path.name}: {path.stat().st_size / 1024:.0f} KB")


def area_plana(anel):
    a = np.asarray(anel)
    return 0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])


def geo(raiz: Path, out: Path, nomes: dict):
    g = json.load(open(raiz / "dados/brutos/referencia/geojs-23-mun.json", encoding="utf-8"))
    feats = []
    for f in g["features"]:
        aneis = []
        for k, anel in enumerate(f["geometry"]["coordinates"]):
            # 3 casas (~110 m): abaixo de 1 pixel na escala do mapa; remove pontos repetidos após arredondar
            anel = [[round(x, 3), round(y, 3)] for x, y in anel]
            anel = [pt for i, pt in enumerate(anel) if i == 0 or pt != anel[i - 1]]
            # d3-geo: anel externo no sentido horário (área plana negativa), buracos anti-horário
            if (area_plana(anel) > 0) == (k == 0):
                anel = anel[::-1]
            aneis.append(anel)
        ibge = str(f["properties"]["id"]).zfill(7)
        feats.append({"type": "Feature", "id": ibge, "properties": {"nome": nomes[ibge]},
                      "geometry": {"type": "Polygon", "coordinates": aneis}})
    assert len(feats) == 184
    salvar({"type": "FeatureCollection", "features": feats}, out / "geo.json")


def base(raiz: Path) -> pd.DataFrame:
    m = pd.read_csv(raiz / "dados/processados/municipal.csv", dtype={"ibge": str}, usecols=["ibge", "municipio", "pop2021", "pop2022"])
    u = pd.read_csv(raiz / "dados/processados/microdados_municipal.csv", dtype={"ibge": str})
    d = m.merge(u.drop(columns=["municipio", "pop2022"]), on="ibge", validate="1:1").set_index("ibge")
    assert len(d) == 184
    d["pessoas_d1_tot"] = d.pessoas_d1 + d.du_res          # pessoas com 1ª dose (D1 + dose única)
    d["pessoas_comp_tot"] = d.com_d2 + d.du_res            # esquema completo (D1 e D2 + dose única)
    d["doses_d1_tot"] = d.d1_res + d.du_res                # REGISTROS de 1ª dose (com duplicidade)
    d["cob_pessoas_d1"] = d.pessoas_d1_tot / d.pop2022
    d["cob_pessoas_comp"] = d.pessoas_comp_tot / d.pop2022
    d["rmf"] = d.municipio.isin(RMF)
    assert d.rmf.sum() == 19
    return d


def cap1(d: pd.DataFrame, raiz: Path, out: Path):
    s = pd.read_csv(raiz / "dados/processados/microdados_serie_semanal.csv", dtype={"ibge": str})
    semanas = sorted(s.semana.unique())
    acum = {}
    for col in ("novas_d1", "novas_comp"):
        t = s.pivot_table(index="semana", columns="ibge", values=col, aggfunc="sum", fill_value=0)
        acum[col] = t.reindex(index=semanas, columns=d.index, fill_value=0).cumsum()
    P = d.pop2022
    cov = acum["novas_comp"] / P
    est_d1 = acum["novas_d1"].sum(axis=1) / P.sum()
    est_comp = acum["novas_comp"].sum(axis=1) / P.sum()
    p10, p50, p90 = cov.quantile(0.1, axis=1), cov.quantile(0.5, axis=1), cov.quantile(0.9, axis=1)

    def ate(serie, data):
        return serie[serie.index <= data].iloc[-1]

    dez21 = ate(cov, "2021-12-31")
    fim = cov.iloc[-1]
    rho = stats.spearmanr(dez21, fim)[0]
    largura = p90 - p10

    dia = pd.read_csv(raiz / "dados/processados/microdados_doses_diarias.csv")
    classes = [c for c in ("D1", "D2", "DU", "REF", "SEM_DOSE") if c in dia]
    dia["total"] = dia[classes].sum(axis=1)
    picos = dia.nlargest(5, "total")[["data", "total"]]

    # semana em que a faixa P10–P90 parou de abrir (90% da largura final)
    congela = largura[largura >= 0.9 * largura.iloc[-1]].index[0]
    obj = {
        "semanas": semanas,
        "estado_d1": [r(x) for x in est_d1], "estado_comp": [r(x) for x in est_comp],
        "p10": [r(x) for x in p10], "p50": [r(x) for x in p50], "p90": [r(x) for x in p90],
        "marcos": {
            "largura_jun21": r(ate(largura, "2021-06-30")), "largura_dez21": r(ate(largura, "2021-12-31")),
            "largura_fim": r(largura.iloc[-1]), "semana_congela": congela,
            "rho_dez21_fim": r(rho, 3),
            "estado_d1_fim": r(est_d1.iloc[-1]), "estado_comp_fim": r(est_comp.iloc[-1]),
            "estado_comp_dez21": r(ate(est_comp, "2021-12-31")),
        },
        "doses_total": int(dia.total.sum()),
        "pessoas_d1": int(d.pessoas_d1_tot.sum()), "pessoas_comp": int(d.pessoas_comp_tot.sum()),
        "pop2022": int(P.sum()),
        "calendario": [[a, int(b)] for a, b in zip(dia.data, dia.total)],
        "picos": [{"data": a, "doses": int(b)} for a, b in zip(picos.data, picos.total)],
        "periodo": [dia.data.min(), dia.data.max()],
    }
    salvar(obj, out / "cap1.json")
    return obj["marcos"], obj["doses_total"]


def cap3(d: pd.DataFrame, out: Path):
    a = d.doses_d1_tot / d.pop2021            # (a) registros ÷ estimativa 2021  (o erro)
    b = d.doses_d1_tot / d.pop2022            # (b) registros ÷ Censo 2022
    c = d.cob_pessoas_d1                       # (c) pessoas ÷ Censo 2022
    c21 = d.pessoas_d1_tot / d.pop2021
    robusto = (c > 1) & (c21 > 1)             # acima de 100% com os dois denominadores
    excesso = int(((d.pessoas_d1_tot - d.pop2022)[c > 1]).sum())
    assert excesso == EXCESSO_VERIFICACOES, (excesso, EXCESSO_VERIFICACOES)
    interior = ~d.index.isin(["2304400"])
    fz, cat = "2304400", d.index[d.municipio == "Catarina"][0]
    rank = lambda s, k: int(s.rank(ascending=False, method="min")[k])
    obj = {
        "indicador": "1ª dose (D1 + dose única), por residência",
        "municipios": [{"id": k, "a": r(a[k]), "b": r(b[k]), "c": r(c[k]), "robusto": bool(robusto[k]),
                        "sensivel": k in SENSIVEL_DENOMINADOR,
                        "dup": r(d.d1_res[k] / d.pessoas_d1[k], 3)} for k in d.index],
        "contagens": {"a": int((a > 1).sum()), "b": int((b > 1).sum()), "c": int((c > 1).sum()),
                      "robusto": int(robusto.sum())},
        "excesso": {"pessoas": excesso, "pct_pop": r(excesso / d.pop2022.sum(), 4)},
        "destaques": {
            "catarina": {"id": cat, "a": r(a[cat]), "c": r(c[cat]), "rank_a": rank(a, cat), "rank_c": rank(c, cat),
                         "razao_pop": r(d.pop2022[cat] / d.pop2021[cat], 3)},
            "fortaleza": {"id": fz, "a": r(a[fz]), "c": r(c[fz]), "rank_a": rank(a, fz), "rank_c": rank(c, fz),
                          "interior_a": r(d.doses_d1_tot[interior].sum() / d.pop2021[interior].sum()),
                          "interior_c": r(d.pessoas_d1_tot[interior].sum() / d.pop2022[interior].sum())},
            "itaitinga": {"id": "2306256", "a": r(a["2306256"]), "c": r(c["2306256"]),
                          "pop2021": int(d.pop2021["2306256"]), "pop2022": int(d.pop2022["2306256"])},
        },
    }
    salvar(obj, out / "cap3.json")
    return obj["contagens"], obj["destaques"]


# ----------------------------------------------------------------------------
# Fase 2: capítulos 2, 4 e 5
# ----------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from analise_politica import spearman_parcial  # noqa: E402
import verificacoes_finais as vf               # noqa: E402

CTRL = ["log_pop2022", "razao_pop22_21"]                                   # porte + erro de população
CTRL_URB = ["log_pop2022", "log_densidade", "alfab15", "renda_mediana_pc"]  # porte e urbanização (eixo político)
MODELO = ["log_pop2022", "razao_pop22_21", "renda_mediana_pc", "pct_rural", "pct_evangelicos",
          "esf_10mil_21", "pct_bolsonaro_2018"]                            # mesmo de analise_eixos.py


def explicativas(d: pd.DataFrame, raiz: Path) -> pd.DataFrame:
    b = pd.read_csv(raiz / "dados/processados/base_analise.csv", dtype={"ibge": str}).set_index("ibge")
    cols = ["renda_mediana_pc", "dist_fortaleza_km", "pct_bolsonaro_2018", "var_bolsonaro_18_22", "esf_10mil_21",
            "flu_idosos_cob", "log_pop2022", "log_densidade", "alfab15", "razao_pop22_21", "pct_rural",
            "pct_evangelicos", "vizinhos"]
    e = d.join(b[cols], how="left")
    assert e[cols[:-1]].notna().all().all()
    e["ref_hab"] = e.ref_res / e.pop2022          # reforço: DOSES por habitante (não pessoas)
    # semana em que as pessoas com 1ª dose chegaram a 50% da população do Censo (ritmo)
    s = pd.read_csv(raiz / "dados/processados/microdados_serie_semanal.csv", dtype={"ibge": str})
    acum = s.pivot_table(index="semana", columns="ibge", values="novas_d1", aggfunc="sum", fill_value=0).cumsum() / e.pop2022
    e["dias_d1_50"] = acum.apply(lambda c: (pd.Timestamp(c[c >= 0.5].index[0]) - pd.Timestamp("2021-01-17")).days)
    return e


def corr(e, x, y, ctrl):
    rho, p = stats.spearmanr(e[x], e[y])
    rp, pp, n = spearman_parcial(e, x, y, [c for c in ctrl if c != x])
    return {"rho": r(rho, 2), "p": r(p, 4), "rho_parcial": r(rp, 2), "p_parcial": r(pp, 4), "n": n}


def cap2(e: pd.DataFrame, out: Path):
    fz = "2304400"
    rmf = e[e.rmf]
    sus = [
        {"chave": "renda", "var": "renda_mediana_pc", "titulo": "A pobreza",
         "eixo": "Renda domiciliar per capita mediana, 2022 (R$)", "fmt": "reais",
         "stats": corr(e, "renda_mediana_pc", "cob_pessoas_comp", CTRL),
         "ritmo": corr(e, "renda_mediana_pc", "dias_d1_50", CTRL)},
        {"chave": "interior", "var": "dist_fortaleza_km", "titulo": "O interior",
         "eixo": "Distância até Fortaleza (km)", "fmt": "km",
         "stats": corr(e, "dist_fortaleza_km", "cob_pessoas_comp", CTRL)},
        {"chave": "politica", "var": "pct_bolsonaro_2018", "titulo": "A política",
         "eixo": "Votos válidos em Bolsonaro, 2º turno de 2018 (%)", "fmt": "pct100",
         "stats": corr(e, "pct_bolsonaro_2018", "cob_pessoas_comp", CTRL_URB),
         "controles_vs_voto": {c: r(stats.spearmanr(e.pct_bolsonaro_2018, e[c])[0], 2)
                               for c in ["log_pop2022", "log_densidade", "alfab15"]}},
        {"chave": "saude", "var": "esf_10mil_21", "titulo": "A rede de saúde",
         "eixo": "Equipes de Saúde da Família por 10 mil habitantes (dez/21)", "fmt": "dec1",
         "stats": corr(e, "esf_10mil_21", "cob_pessoas_comp", CTRL),
         "rho_porte": r(stats.spearmanr(e.esf_10mil_21, e.log_pop2022)[0], 2)},
        {"chave": "habito", "var": "flu_idosos_cob", "titulo": "O hábito",
         "eixo": "Cobertura da vacina da gripe em idosos, 2019", "fmt": "pct",
         "stats": corr(e, "flu_idosos_cob", "cob_pessoas_comp", CTRL),
         "n_teto": int((e.flu_idosos_cob >= 0.9).sum())},
    ]
    obj = {
        "y": "Esquema completo (pessoas ÷ Censo 2022)",
        "municipios": [{"id": k, "y": r(e.cob_pessoas_comp[k]), **{s["chave"]: r(e[s["var"]][k], 4) for s in sus}}
                       for k in e.index],
        "suspeitos": [{k: v for k, v in s.items() if k != "var"} for s in sus],
        "fortaleza": {"comp": r(e.cob_pessoas_comp[fz]), "abandono": r(e.abandono_individual[fz]),
                      "rank_abandono_rmf": int(rmf.abandono_individual.rank(method="min")[fz]), "n_rmf": len(rmf),
                      "interior_comp": r(e[~e.index.isin([fz])].pessoas_comp_tot.sum() / e[~e.index.isin([fz])].pop2022.sum())},
    }
    assert obj["fortaleza"]["rank_abandono_rmf"] == 1, "o texto diz que Fortaleza tem o menor abandono da RMF"
    salvar(obj, out / "cap2.json")
    return {s["chave"]: s["stats"] for s in sus}


def moran_i(y: np.ndarray, W: np.ndarray) -> float:
    z = y - y.mean()
    return float((len(y) / W.sum()) * (z @ W @ z) / (z @ z))


def cap4(e: pd.DataFrame, raiz: Path, out: Path):
    v = vf.carregar(raiz)                    # mesma base e mesmas regras de verificacoes_finais.py
    x = vf.v1_comecaram_atras(v, [])         # decomposição e perfis dos 13, idênticos ao relatório
    soma = x[["parte_d1", "parte_aband"]].sum()
    perfis = {"os dois": "dois", "começou atrás": "atras", "não voltou": "naovoltou"}
    ids = list(e.index)
    pos = {k: i for i, k in enumerate(ids)}
    A = np.zeros((len(ids), len(ids)))
    for k, viz in e.vizinhos.items():
        for j in str(viz).split(";"):
            if j in pos:
                A[pos[k], pos[j]] = 1
    W = A / A.sum(axis=1, keepdims=True)
    moran = {nome: r(moran_i(e[c].to_numpy(float), W), 3) for nome, c in
             [("cobertura", "cob_pessoas_comp"), ("voto", "pct_bolsonaro_2018"), ("renda", "renda_mediana_pc")]}
    obj = {
        "criterio": "esquema completo < 70% (registros ÷ Censo 2022), como em verificacoes_finais.md",
        "treze": [{"id": k, "nome": e.municipio[k], "d1": r(row.cob_pessoas_d1), "comp": r(row.cob_pessoas_comp),
                   "abandono": r(row.abandono_individual), "perfil": perfis[row.perfil], "pct_gap_d1": r(row.pct_gap_d1, 1),
                   "rank_d1": int(row.rank_d1), "rank_aband": int(row.rank_aband)} for k, row in x.iterrows()],
        "ref": {"d1": r(v[~v.baixo].cob_pessoas_d1.median()), "retencao": r(1 - v[~v.baixo].abandono_individual.median()),
                "comp": r(v[~v.baixo].cob_pessoas_comp.median()), "abandono": r(v[~v.baixo].abandono_individual.median())},
        "decomp": {"pct_d1": r(soma.parte_d1 / soma.sum(), 3), "pct_aband": r(soma.parte_aband / soma.sum(), 3)},
        "perfis": {perfis[k]: int(n) for k, n in x.perfil.value_counts().items()},
        "grupos": {"baixo_d1": r(v[v.baixo].cob_pessoas_d1.median()), "baixo_aband": r(v[v.baixo].abandono_individual.median()),
                   "baixo_comp": r(v[v.baixo].cob_pessoas_comp.median())},
        "moran": moran,
        "mapas": [{"id": k, "cobertura": r(e.cob_pessoas_comp[k]), "voto": r(e.pct_bolsonaro_2018[k], 2),
                   "renda": r(e.renda_mediana_pc[k], 2)} for k in ids],
        "n_pessoas_abaixo_70": int((e.cob_pessoas_comp < 0.7).sum()),
    }
    salvar(obj, out / "cap4.json")
    return obj["decomp"], obj["perfis"], moran


def cap5(e: pd.DataFrame, out: Path):
    p10, p90 = e.ref_hab.quantile(0.1), e.ref_hab.quantile(0.9)
    ctrl = CTRL + ["pct_evangelicos", "renda_mediana_pc", "esf_10mil_21"]
    # R² da regressão em postos, um representante por eixo (como em analise_eixos.py), por desfecho
    r2 = {}
    for y in ["cob_pessoas_comp", "cob_pessoas_d1", "abandono_individual", "ref_hab", "dias_d1_50"]:
        t = e[[y] + MODELO].rank()
        X = np.column_stack([np.ones(len(t)), t[MODELO].to_numpy()])
        beta, *_ = np.linalg.lstsq(X, t[y].to_numpy(), rcond=None)
        res = t[y].to_numpy() - X @ beta
        r2[y] = r(1 - res.var() / t[y].var(ddof=0), 3)
    obj = {
        "municipios": [{"id": k, "ref": r(e.ref_hab[k]), "var": r(e.var_bolsonaro_18_22[k], 2)} for k in e.index],
        "p10": r(p10, 3), "p90": r(p90, 3), "razao_p90_p10": r(p90 / p10, 2),
        "var_bolsonaro": corr(e, "var_bolsonaro_18_22", "ref_hab", ctrl),
        "controles": ctrl, "r2": r2, "r2_max": max(r2.values()),
    }
    salvar(obj, out / "cap5.json")
    return obj["razao_p90_p10"], obj["var_bolsonaro"], r2


# ----------------------------------------------------------------------------
# Fase 3: capítulo 7 (Explore)
# ----------------------------------------------------------------------------
def cap7(e: pd.DataFrame, raiz: Path, out: Path):
    v = vf.carregar(raiz)
    perfis = {"os dois": "dois", "começou atrás": "atras", "não voltou": "naovoltou"}
    perfil = {k: perfis[p] for k, p in vf.v1_comecaram_atras(v, []).perfil.items()}
    c3 = (e.pessoas_d1_tot / e.pop2022 > 1) & (e.pessoas_d1_tot / e.pop2021 > 1)

    # série mensal (fim de cada mês) da cobertura acumulada, em milésimos, por município e do estado
    s = pd.read_csv(raiz / "dados/processados/microdados_serie_semanal.csv", dtype={"ibge": str})
    ac = {c: s.pivot_table(index="semana", columns="ibge", values=c, aggfunc="sum", fill_value=0)
          .reindex(columns=e.index, fill_value=0).cumsum() for c in ("novas_d1", "novas_comp")}
    idx = pd.to_datetime(ac["novas_d1"].index)
    meses = pd.period_range(idx.min(), idx.max(), freq="M")
    pos = [int(np.searchsorted(idx, p.end_time, side="right")) - 1 for p in meses]
    serie = {c: ac[c].iloc[pos] for c in ac}
    estado = {c: [r(x, 4) for x in serie[c].sum(axis=1) / e.pop2022.sum()] for c in serie}

    vars_ = {  # chave curta: (coluna, rótulo, unidade)
        "d1": ("cob_pessoas_d1", "1ª dose", "pct"),
        "comp": ("cob_pessoas_comp", "Esquema completo", "pct"),
        "aband": ("abandono_individual", "Abandono (1ª dose sem 2ª)", "pct"),
        "ref": ("ref_hab", "Reforços por habitante", "dec2"),
        "renda": ("renda_mediana_pc", "Renda per capita mediana, 2022", "reais"),
        "voto": ("pct_bolsonaro_2018", "Voto em Bolsonaro, 2º turno 2018", "pct100"),
        "varvoto": ("var_bolsonaro_18_22", "Variação do voto em Bolsonaro, 2018→2022 (p.p.)", "dec1"),
        "esf": ("esf_10mil_21", "Equipes de Saúde da Família por 10 mil hab.", "dec1"),
        "dist": ("dist_fortaleza_km", "Distância até Fortaleza (km)", "km"),
        "flu": ("flu_idosos_cob", "Vacina da gripe em idosos, 2019", "pct"),
        "evang": ("pct_evangelicos", "Evangélicos (%)", "pct100"),
        "rural": ("pct_rural", "População rural (%)", "pct100"),
        "pop": ("pop2022", "População (Censo 2022)", "int"),
    }
    obj = {
        "variaveis": {k: {"rot": rot, "fmt": f} for k, (_, rot, f) in vars_.items()},
        "meses": [str(p) for p in meses],
        "estado": {"d1": estado["novas_d1"], "comp": estado["novas_comp"]},
        "municipios": [{
            "id": k, "nome": e.municipio[k], "rmf": bool(e.rmf[k]),
            **{c: r(e[col][k], 5) for c, (col, _, _) in vars_.items()},
            "perfil": perfil.get(k), "sensivel": k in SENSIVEL_DENOMINADOR, "acima100_robusto": bool(c3[k]),
            "s_d1": [int(round(1000 * x)) for x in serie["novas_d1"][k] / e.pop2022[k]],
            "s_comp": [int(round(1000 * x)) for x in serie["novas_comp"][k] / e.pop2022[k]],
        } for k in e.index],
    }
    assert sum(1 for m in obj["municipios"] if m["perfil"]) == 13
    salvar(obj, out / "cap7.json")


def municipios(d: pd.DataFrame, out: Path):
    salvar([{"id": k, "nome": d.municipio[k], "pop2021": int(d.pop2021[k]), "pop2022": int(d.pop2022[k]),
             "rmf": bool(d.rmf[k])} for k in d.index], out / "municipios.json")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    out = raiz / "json"
    out.mkdir(parents=True, exist_ok=True)
    d = base(raiz)
    print("Gerando JSONs em", out)
    geo(raiz, out, d.municipio.to_dict())
    municipios(d, out)
    marcos, doses = cap1(d, raiz, out)
    cont, dest = cap3(d, out)
    e = explicativas(d, raiz)
    st2 = cap2(e, out)
    decomp, perfis, moran = cap4(e, raiz, out)
    razao_ref, vb, r2 = cap5(e, out)
    cap7(e, raiz, out)
    print("\nCifras calculadas (conferir com o texto):")
    print(f"  cap. 2 (pessoas, esq. completo): {st2}")
    print(f"  cap. 4: decomposição {decomp}; perfis {perfis}; I de Moran {moran}")
    print(f"  cap. 5: reforço P90/P10 = {razao_ref}; variação do voto × reforço {vb}; R² {r2}")
    print(f"  doses a residentes do CE (17/01/2021–16/04/2024): {doses:,}")
    print(f"  marcos cap. 1: {marcos}")
    print(f"  > 100% por estado do mapa (cap. 3): {cont}")
    print(f"  destaques cap. 3: {dest}")


if __name__ == "__main__":
    main()
