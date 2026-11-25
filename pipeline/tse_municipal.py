"""Agrega resultados do TSE por município do Ceará e gera dados/processados/tse_municipal.csv.

Uso:
    python pipeline/tse_municipal.py            # lê de dados/brutos/tse/
    python pipeline/tse_municipal.py --tse-dir OUTRA_PASTA --raiz .

Arquivos em --tse-dir (.csv ou .csv.gz), extraídos dos zips de dadosabertos.tse.jus.br:
    votacao_candidato_munzona_2018_BR.csv   presidente (fica no _BR, não no _CE)
    votacao_candidato_munzona_2022_BR.csv
    votacao_candidato_munzona_2020_CE.csv   prefeito
    detalhe_votacao_munzona_{2018,2022}_BR.csv  comparecimento e brancos/nulos
    consulta_cand_2016_CE.csv, consulta_cand_2020_CE.csv  reeleição (contêm CPF e e-mail de candidatos)
    municipio_tse_ibge.zip                  correspondência de códigos TSE -> IBGE
"""
import argparse
import zipfile
from pathlib import Path

import pandas as pd

LER = dict(sep=";", encoding="latin-1", dtype=str)


def arq(pasta: Path, nome: str) -> Path:
    """Aceita o arquivo como .csv ou compactado (.csv.gz); o pandas descompacta pela extensão."""
    for c in (pasta / nome, pasta / f"{nome}.gz"):
        if c.exists():
            return c
    return pasta / nome
NUM_BOLSONARO = {2018: "17", 2022: "22"}
NUM_PT = "13"


def tabela_codigos(tse_dir: Path) -> pd.DataFrame:
    with zipfile.ZipFile(tse_dir / "municipio_tse_ibge.zip") as z:
        d = pd.read_csv(z.open("municipio_tse_ibge.csv"), **LER)
    d = d[d.SG_UF == "CE"]
    out = pd.DataFrame({
        "cd_tse": d.CD_MUNICIPIO_TSE.str.zfill(5),
        "ibge": d.CD_MUNICIPIO_IBGE.str.zfill(7),
        "municipio": d.NM_MUNICIPIO_IBGE,
    })
    assert len(out) == 184 and out.ibge.is_unique and out.cd_tse.is_unique, len(out)
    return out


def presidente(tse_dir: Path, ano: int, log: list) -> pd.DataFrame:
    cols = ["SG_UF", "CD_MUNICIPIO", "NR_TURNO", "CD_CARGO", "NR_CANDIDATO",
            "QT_VOTOS_NOMINAIS_VALIDOS"]
    d = pd.read_csv(arq(tse_dir, f"votacao_candidato_munzona_{ano}_BR.csv"), usecols=cols, **LER)
    d = d[(d.SG_UF == "CE") & (d.CD_CARGO == "1")].copy()
    d["v"] = d.QT_VOTOS_NOMINAIS_VALIDOS.astype(int)
    d["cd_tse"] = d.CD_MUNICIPIO.str.zfill(5)
    res = {}
    for turno in ("1", "2"):
        t = d[d.NR_TURNO == turno]
        validos = t.groupby("cd_tse").v.sum()
        bolso = t[t.NR_CANDIDATO == NUM_BOLSONARO[ano]].groupby("cd_tse").v.sum()
        pt = t[t.NR_CANDIDATO == NUM_PT].groupby("cd_tse").v.sum()
        res[f"pct_bolsonaro_{'1t_' if turno == '1' else ''}{ano}"] = 100 * bolso / validos
        if turno == "2":
            res[f"votos_validos_2t_{ano}"] = validos
            tot_b, tot_v, tot_pt = bolso.sum(), validos.sum(), pt.sum()
            log.append(f"- Presidente {ano}, 2º turno, CE: {t.cd_tse.nunique()} municípios; "
                       f"Bolsonaro {tot_b:,} ({100*tot_b/tot_v:.2f}%), "
                       f"{'Haddad' if ano == 2018 else 'Lula'} {tot_pt:,} ({100*tot_pt/tot_v:.2f}%), "
                       f"válidos {tot_v:,}; soma dos dois = válidos? {tot_b + tot_pt == tot_v}")
        else:
            tot_b, tot_v = bolso.sum(), validos.sum()
            log.append(f"- Presidente {ano}, 1º turno, CE: Bolsonaro {100*tot_b/tot_v:.2f}% dos válidos")
    return pd.DataFrame(res)


def prefeito_2020(tse_dir: Path, log: list) -> pd.DataFrame:
    d = pd.read_csv(arq(tse_dir, "votacao_candidato_munzona_2020_CE.csv"), **LER)
    d = d[d.CD_CARGO == "11"].copy()
    d["v"] = d.QT_VOTOS_NOMINAIS_VALIDOS.astype(int)
    d["cd_tse"] = d.CD_MUNICIPIO.str.zfill(5)

    # Suplementares: registrar o vencedor, mas não substituir a ordinária
    sup = d[d.CD_TIPO_ELEICAO == "1"]
    sup_agg = (sup.groupby(["cd_tse", "SQ_CANDIDATO", "SG_PARTIDO", "DS_SIT_TOT_TURNO", "DT_ELEICAO"])
               .v.sum().reset_index())
    sup_eleito = sup_agg[sup_agg.DS_SIT_TOT_TURNO == "ELEITO"].set_index("cd_tse")

    ordi = d[d.CD_TIPO_ELEICAO == "2"]
    agg = (ordi.groupby(["cd_tse", "NR_TURNO", "SQ_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO",
                         "DS_SIT_TOT_TURNO"]).v.sum().reset_index())
    linhas = []
    for cd, g in agg.groupby("cd_tse"):
        turno = g.NR_TURNO.max()  # turno decisivo
        g = g[g.NR_TURNO == turno].sort_values("v", ascending=False)
        eleitos = g[g.DS_SIT_TOT_TURNO == "ELEITO"]
        validos = g.v.sum()
        n_eleitos = len(eleitos)
        segundo = lambda e: g[g.SQ_CANDIDATO != e.SQ_CANDIDATO].v.max() if len(g) > 1 else 0
        linha = {"cd_tse": cd, "prefeito_turno_2020": int(turno),
                 "prefeito_n_candidatos_2020": len(g), "prefeito_n_eleitos_2020": n_eleitos,
                 "mais_votado_partido_2020": g.iloc[0].SG_PARTIDO}
        if n_eleitos == 1:
            e = eleitos.iloc[0]
            linha.update({
                "prefeito_status_2020": "eleito",
                "prefeito_nome_2020": e.NM_URNA_CANDIDATO,
                "prefeito_partido_2020": e.SG_PARTIDO,
                "prefeito_sq_2020": e.SQ_CANDIDATO,
                "prefeito_pct_votos_2020": 100 * e.v / validos if validos else None,
                "prefeito_margem_2020": 100 * (e.v - segundo(e)) / validos if validos else None,
            })
        else:  # sinalizar, não descartar nem inventar eleito
            linha["prefeito_status_2020"] = f"{n_eleitos}_eleitos_na_ordinaria"
        linhas.append(linha)
    out = pd.DataFrame(linhas).set_index("cd_tse")
    out["suplementar_2020_21"] = out.index.isin(sup.cd_tse)
    out["suplementar_partido"] = sup_eleito.SG_PARTIDO.reindex(out.index)
    out["suplementar_data"] = sup_eleito.DT_ELEICAO.reindex(out.index)
    log.append(f"- Prefeito 2020 (ordinária): {len(out)} municípios; "
               f"{(out.prefeito_n_eleitos_2020 == 1).sum()} com exatamente 1 eleito; "
               f"{(out.prefeito_n_eleitos_2020 == 0).sum()} sem eleito; "
               f"2º turno em {(out.prefeito_turno_2020 == 2).sum()} "
               f"({', '.join(sorted(out.index[out.prefeito_turno_2020 == 2]))}); "
               f"candidato único em {(out.prefeito_n_candidatos_2020 == 1).sum()}")
    log.append(f"- Eleições suplementares para prefeito (2021–2023): {sup.cd_tse.nunique()} municípios")
    return out


def comparecimento(tse_dir: Path, ano: int, log: list) -> pd.DataFrame | None:
    f = arq(tse_dir, f"detalhe_votacao_munzona_{ano}_BR.csv")
    if not f.exists():
        log.append(f"- {f.name} ausente: sem comparecimento {ano}")
        return None
    d = pd.read_csv(f, usecols=["SG_UF", "CD_MUNICIPIO", "NR_TURNO", "CD_CARGO", "QT_APTOS",
                                "QT_COMPARECIMENTO", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS"], **LER)
    d = d[(d.SG_UF == "CE") & (d.CD_CARGO == "1")].copy()
    for c in ["QT_APTOS", "QT_COMPARECIMENTO", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS"]:
        d[c] = d[c].astype(int)
    d["cd_tse"] = d.CD_MUNICIPIO.str.zfill(5)
    out = {}
    for t in ("1", "2"):
        g = d[d.NR_TURNO == t].groupby("cd_tse")[["QT_APTOS", "QT_COMPARECIMENTO", "QT_VOTOS_BRANCOS",
                                                    "QT_TOTAL_VOTOS_NULOS"]].sum()
        suf = f"{'1t_' if t == '1' else ''}{ano}"
        out[f"comparecimento_{suf}"] = 100 * g.QT_COMPARECIMENTO / g.QT_APTOS
        if t == "2":
            out[f"brancos_nulos_{ano}"] = 100 * (g.QT_VOTOS_BRANCOS + g.QT_TOTAL_VOTOS_NULOS) / g.QT_COMPARECIMENTO
            out[f"aptos_{ano}"] = g.QT_APTOS
            log.append(f"- Comparecimento {ano}, 2º turno, CE: {100*g.QT_COMPARECIMENTO.sum()/g.QT_APTOS.sum():.2f}% "
                       f"({g.QT_COMPARECIMENTO.sum():,} de {g.QT_APTOS.sum():,} aptos; {len(g)} municípios)")
    return pd.DataFrame(out)


def reeleicao_2020(tse_dir: Path, pref: pd.DataFrame, log: list) -> pd.Series | None:
    """Prefeito eleito em 2020 que também foi eleito prefeito em 2016 no mesmo município.
    Liga por título de eleitor (ou CPF) só internamente; nenhum identificador vai para a saída."""
    f16 = arq(tse_dir, "consulta_cand_2016_CE.csv")
    if not f16.exists():
        log.append("- consulta_cand_2016_CE.csv ausente: sem reeleição")
        return None
    cols = ["SG_UE", "CD_CARGO", "SQ_CANDIDATO", "NR_CPF_CANDIDATO", "NR_TITULO_ELEITORAL_CANDIDATO",
            "DS_SIT_TOT_TURNO"]
    c20 = pd.read_csv(arq(tse_dir, "consulta_cand_2020_CE.csv"), usecols=cols, **LER)
    c16 = pd.read_csv(f16, usecols=cols, **LER)
    e16 = c16[(c16.CD_CARGO == "11") & (c16.DS_SIT_TOT_TURNO == "ELEITO")]
    chave16 = set(zip(e16.SG_UE.str.zfill(5), e16.NR_TITULO_ELEITORAL_CANDIDATO)) | \
        set(zip(e16.SG_UE.str.zfill(5), e16.NR_CPF_CANDIDATO))
    c20 = c20.drop_duplicates("SQ_CANDIDATO").set_index("SQ_CANDIDATO")
    res = {}
    for cd, sq in pref.prefeito_sq_2020.dropna().items():
        if sq not in c20.index:
            continue
        r = c20.loc[sq]
        res[cd] = (cd, r.NR_TITULO_ELEITORAL_CANDIDATO) in chave16 or (cd, r.NR_CPF_CANDIDATO) in chave16
    s = pd.Series(res, name="prefeito_reeleito_2020")
    log.append(f"- Reeleição 2020: {s.sum()} prefeitos reeleitos de {len(s)} eleitos com cadastro "
               f"(comparação com os eleitos de 2016 por título/CPF; {e16.SG_UE.nunique()} municípios com eleito em 2016)")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tse-dir", default=Path("dados/brutos/tse"), type=Path)
    ap.add_argument("--raiz", default=Path("."), type=Path)
    a = ap.parse_args()

    log = ["# Validação — tse_municipal.csv", ""]
    cod = tabela_codigos(a.tse_dir).set_index("cd_tse")
    p18 = presidente(a.tse_dir, 2018, log)
    p22 = presidente(a.tse_dir, 2022, log)
    pref = prefeito_2020(a.tse_dir, log)

    df = cod.join(p18).join(p22).join(pref)
    for extra in (comparecimento(a.tse_dir, 2018, log), comparecimento(a.tse_dir, 2022, log),
                  reeleicao_2020(a.tse_dir, pref, log)):
        if extra is not None:
            df = df.join(extra)
    df["prefeito_status_2020"] = df.prefeito_status_2020.fillna("sem_votacao_no_arquivo")
    for _, r in df[df.prefeito_status_2020 != "eleito"].iterrows():
        log.append(f"  - {r.municipio}: {r.prefeito_status_2020}; suplementar={r.suplementar_2020_21} "
                   f"({r.suplementar_partido}, {r.suplementar_data})")
    df["var_bolsonaro_18_22"] = df.pct_bolsonaro_2022 - df.pct_bolsonaro_2018

    for c in ["pct_bolsonaro_2018", "pct_bolsonaro_2022", "prefeito_partido_2020"]:
        falta = df.index[df[c].isna()].tolist()
        log.append(f"- Sem valor em {c}: {len(falta)} {[cod.municipio[x] for x in falta]}")
    log.append(f"- Linhas: {len(df)}; ibge único: {df.ibge.is_unique}")

    df = df.reset_index()
    cols = ["ibge", "cd_tse", "municipio"] + [c for c in df.columns if c not in ("ibge", "cd_tse", "municipio")]
    df[cols].to_csv(a.raiz / "dados/processados/tse_municipal.csv", index=False, float_format="%.4f")
    (a.raiz / "relatorios/tse_validacao.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
