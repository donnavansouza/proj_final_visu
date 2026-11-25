"""Microdados de vacinação Covid (OpenDataSUS) → recorte do Ceará e indicadores por município.

Etapa 1 — filtrar (lê em blocos; aceita .csv ou .zip; pode ser interrompida e retomada):
    python pipeline/microdados_vacinacao.py filtrar ARQ1 ARQ2 ... --saida dados/brutos/microdados_CE
Guarda só linhas em que o município de RESIDÊNCIA ou o de APLICAÇÃO é do CE, e só as 6 colunas
usadas adiante (ver compactar()), em <saida>/parte_<arquivo>.csv.gz. O recorte do projeto está em
dados/brutos/microdados_CE/ (pasta padrão). Arquivos já concluídos ficam em <saida>/concluidos.txt.

Etapa 2 — agregar:
    python pipeline/microdados_vacinacao.py agregar --saida dados/brutos/microdados_CE
Gera em dados/:
    microdados_doses_res_aplic.csv  doses por (município de residência, município de aplicação, dose)
    microdados_municipal.csv        por município do CE: doses por residência e por aplicação,
                                    saldo de "importação", abandono individual (pessoas com D1 sem D2)
    microdados_validacao.md
"""
import argparse
import csv
import gzip
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

# nome lógico -> nomes possíveis no arquivo (comparação sem maiúsculas)
COLUNAS = {
    "paciente_id": ["paciente_id"],
    "idade": ["paciente_idade"],
    "res_ibge": ["paciente_endereco_coibgemunicipio"],
    "res_uf": ["paciente_endereco_uf"],
    "est_ibge": ["estabelecimento_municipio_codigo"],
    "est_uf": ["estabelecimento_uf"],
    "data": ["vacina_dataaplicacao"],
    "dose": ["vacina_descricao_dose"],
    "vacina": ["vacina_nome"],
}
BLOCO = 500_000
INICIO, FIM = "2021-01-17", "2024-04-16"  # mesmo período do processed_CE (covid19br-vac)


def abrir_texto(path: Path):
    """Devolve um fluxo de texto para .csv, .csv.gz ou o primeiro .csv dentro de um .zip."""
    if path.suffix.lower() == ".zip":
        z = zipfile.ZipFile(path)
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(nomes) != 1:
            raise SystemExit(f"{path.name}: esperava 1 CSV dentro do zip, achei {nomes}")
        bruto = z.open(nomes[0])
    elif path.suffix.lower() == ".gz":
        bruto = gzip.open(path, "rb")
    else:
        bruto = open(path, "rb")
    return io.TextIOWrapper(bruto, encoding="utf-8", errors="replace", newline="")


def mapear_colunas(cabecalho: list[str]) -> dict:
    baixo = {c.strip().strip('"').lower(): c for c in cabecalho}
    achadas, faltam = {}, []
    for logico, opcoes in COLUNAS.items():
        real = next((baixo[o] for o in opcoes if o in baixo), None)
        if real is None:
            faltam.append(logico)
        else:
            achadas[real] = logico
    if {"paciente_id", "res_ibge", "est_ibge", "dose", "data"} & set(faltam):
        raise SystemExit(f"Colunas essenciais ausentes: {faltam}.\nCabeçalho do arquivo: {cabecalho}")
    if faltam:
        print(f"  aviso: colunas opcionais ausentes: {faltam}")
    return achadas


# Formato do recorte guardado no projeto: só as 6 colunas que as etapas seguintes leem, e o
# identificador do paciente truncado em 16 caracteres hexadecimais (64 bits). O original já é um
# hash anonimizado de 64 caracteres; com ~9 milhões de pessoas, a chance de duas colidirem nos
# 64 bits é da ordem de 1 em 500 mil. Resultado: ~63% menor, mesmos números.
COLUNAS_RECORTE = ["paciente_id", "res_ibge", "est_ibge", "data", "dose", "vacina"]


def compactar(b: pd.DataFrame) -> pd.DataFrame:
    b = b[COLUNAS_RECORTE].copy()
    b["paciente_id"] = b.paciente_id.str[:16]
    return b


def filtrar(arquivos: list[Path], saida: Path):
    saida.mkdir(parents=True, exist_ok=True)
    feitos_txt = saida / "concluidos.txt"
    feitos = set(feitos_txt.read_text(encoding="utf-8").split("\n")) if feitos_txt.exists() else set()
    for arq in arquivos:
        if arq.name in feitos:
            print(f"{arq.name}: já processado, pulando")
            continue
        with abrir_texto(arq) as f:
            primeira = f.readline()
        sep = ";" if primeira.count(";") > primeira.count(",") else ","
        cab = next(csv.reader([primeira], delimiter=sep))
        mapa = mapear_colunas(cab)
        print(f"{arq.name}: separador '{sep}', {len(cab)} colunas; lendo {len(mapa)}")
        destino = saida / f"parte_{arq.stem}.csv.gz"
        tmp = destino.with_suffix(".tmp")
        lidas = guardadas = 0
        with abrir_texto(arq) as f, gzip.open(tmp, "wt", encoding="utf-8", newline="") as out:
            leitor = pd.read_csv(f, sep=sep, usecols=list(mapa), dtype=str, chunksize=BLOCO,
                                 on_bad_lines="warn", quoting=csv.QUOTE_MINIMAL)
            for i, bloco in enumerate(leitor):
                bloco = bloco.rename(columns=mapa)
                lidas += len(bloco)
                ce = bloco.res_ibge.fillna("").str.startswith("23") | bloco.est_ibge.fillna("").str.startswith("23")
                b = compactar(bloco[ce])
                guardadas += len(b)
                b.to_csv(out, index=False, header=(i == 0))
                if i % 10 == 0:
                    print(f"  {lidas:>13,} linhas lidas | {guardadas:>11,} do CE", flush=True)
        tmp.replace(destino)  # só vira definitivo se terminou
        with open(feitos_txt, "a", encoding="utf-8") as f:
            f.write(arq.name + "\n")
        print(f"  OK {arq.name}: {lidas:,} linhas, {guardadas:,} do CE → {destino.name}")


def classificar_dose(s: pd.Series) -> pd.Series:
    t = s.astype("string").fillna("").str.lower().str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.strip()
    out = pd.Series("REF", index=s.index)  # reforços, adicionais, 3a/4a dose etc.
    out[t.str.contains("unica") | (t == "dose")] = "DU"
    out[t.str.startswith("1") & t.str.contains("dose") & ~t.str.contains("refor")] = "D1"
    out[t.str.startswith("2") & t.str.contains("dose") & ~t.str.contains("refor")] = "D2"
    out[t == ""] = "SEM_DOSE"
    return out


def carregar(saida: Path):
    """Lê as partes filtradas → (DataFrame numérico sem duplicatas, linhas de log)."""
    partes = sorted(saida.glob("parte_*.csv.gz"))
    if not partes:
        raise SystemExit(f"Nenhuma parte em {saida}. Rode a etapa 'filtrar' antes.")
    # Economia de memória (~25 mi de linhas): tudo numérico. id do paciente → hash de 64 bits;
    # municípios → inteiro de 6 dígitos; data → dias desde 2021-01-01; dose → classe (categoria fixa).
    classes = pd.CategoricalDtype(["D1", "D2", "DU", "REF", "SEM_DOSE"])
    blocos, doses_brutas = [], pd.Series(dtype="int64")
    excl = {"nao_covid": 0, "fora_periodo": 0}
    for p in partes:
        for b in pd.read_csv(p, usecols=["paciente_id", "res_ibge", "est_ibge", "data", "dose", "vacina"],
                             dtype=str, chunksize=2_000_000):
            # Só Covid (a base traz também influenza "INF3") e só o período do processed_CE
            covid = b.vacina.fillna("").str.upper().str.contains("COVID")
            excl["nao_covid"] += int((~covid).sum())
            b = b[covid]
            dentro = b.data.str[:10].between(INICIO, FIM)
            excl["fora_periodo"] += int((~dentro).sum())
            b = b[dentro]
            doses_brutas = doses_brutas.add(b.dose.fillna("(vazio)").value_counts(), fill_value=0)
            blocos.append(pd.DataFrame({
                "paciente_id": pd.util.hash_array(b.paciente_id.fillna("").to_numpy(object)),
                "res_ibge": pd.to_numeric(b.res_ibge.str[:6], errors="coerce").astype("Int32"),
                "est_ibge": pd.to_numeric(b.est_ibge.str[:6], errors="coerce").astype("Int32"),
                "dia": (pd.to_datetime(b.data.str[:10], errors="coerce") - pd.Timestamp("2021-01-01")).dt.days.astype("Int16"),
                "classe": classificar_dose(b.dose).astype(classes),
            }))
    d = pd.concat(blocos, ignore_index=True)
    del blocos
    log = ["# Validação — microdados de vacinação (recorte CE)", "",
           f"- Partes: {[p.name for p in partes]}",
           f"- Excluídas: {excl['nao_covid']:,} de outras vacinas; {excl['fora_periodo']:,} de Covid fora de {INICIO} a {FIM}",
           f"- Linhas mantidas (Covid, no período, residência ou aplicação no CE): {len(d):,}",
           f"- Datas inválidas/ausentes: {d.dia.isna().sum():,}; período: dia {d.dia.min()} a {d.dia.max()} desde 01/01/2021"]
    n0 = len(d)
    d = d.drop_duplicates()
    log.append(f"- Linhas duplicadas removidas (podem vir de sobreposição entre arquivos): {n0 - len(d):,}")
    tab = doses_brutas.astype(int).sort_values(ascending=False).rename("n").to_frame()
    tab["classe"] = classificar_dose(pd.Series(tab.index, index=tab.index))
    log += ["", "## Mapeamento de vacina_descricao_dose (antes de remover duplicatas)", "",
            tab.head(30).to_markdown(), ""]
    return d, log


def de6_para_ibge(raiz: Path):
    m = pd.read_csv(raiz / "dados/processados/municipal.csv", dtype={"ibge": str, "ibge6": str},
                    usecols=["ibge", "ibge6", "municipio", "pop2022"])
    return m, dict(zip(m.ibge6.astype(int), m.ibge))


def series(saida: Path, raiz: Path):
    """Séries para o site, por PESSOA e município de RESIDÊNCIA.
    dados/processados/microdados_serie_semanal.csv: ibge, semana (início, domingo), novas pessoas com 1ª dose
      (D1 ou DU) e novas pessoas com esquema completo (D2 ou DU), pela data da primeira dose de cada tipo.
    dados/processados/microdados_doses_diarias.csv: doses por dia aplicadas a residentes do CE, por classe."""
    d0, _ = carregar(saida)
    m, de6 = de6_para_ibge(raiz)
    d = d0[d0.res_ibge.isin(de6)]
    base = pd.Timestamp("2021-01-01")

    dia = d.groupby(["dia", "classe"], observed=True).size().unstack(fill_value=0)
    dia.index = base + pd.to_timedelta(dia.index.astype(int), unit="D")
    dia.index.name = "data"
    dia.reset_index().to_csv(raiz / "dados/processados/microdados_doses_diarias.csv", index=False, date_format="%Y-%m-%d")

    # MESMAS definições da etapa agregar (que gerou os números de verificacoes_finais.md):
    #   1ª dose = pessoas com D1 (residência da D1) + doses únicas (DU, por residência da dose)
    #   completo = pessoas com D1 e D2 (data da 1ª D2) + doses únicas
    # Usa todas as linhas, como a agregar (o filtro de residência no CE vem depois).
    p = d0[d0.classe.isin(["D1", "D2"])].copy()
    p["is_d1"] = p.classe == "D1"
    p = p.sort_values("is_d1", ascending=False)
    res = p.groupby("paciente_id").res_ibge.first()
    prim = p[p.is_d1].groupby("paciente_id").dia.min().rename("dia_d1")
    seg = p[~p.is_d1].groupby("paciente_id").dia.min().rename("dia_d2")
    pes = pd.concat([res, prim, seg], axis=1)
    pes = pes[pes.dia_d1.notna() & pes.res_ibge.isin(de6)]
    pes["dia_comp"] = pes.dia_d2  # só quem tem D1 e D2
    du = d[d.classe == "DU"][["res_ibge", "dia"]]
    inicio = (pd.Timestamp(INICIO) - base).days  # semanas a partir de 17/01/2021 (domingo)
    semana = lambda dias: ((dias.astype(int) - inicio) // 7).clip(lower=0)
    du_sem = du.assign(semana=semana(du.dia)).groupby(["res_ibge", "semana"]).size()
    out = []
    for col, nome in (("dia_d1", "novas_d1"), ("dia_comp", "novas_comp")):
        s = pes.dropna(subset=[col])
        cont = s.assign(semana=semana(s[col])).groupby(["res_ibge", "semana"]).size()
        out.append(cont.add(du_sem, fill_value=0).rename(nome))
    serie = pd.concat(out, axis=1).fillna(0).astype(int).reset_index()
    serie["ibge"] = serie.res_ibge.map(de6)
    serie["semana"] = (pd.Timestamp(INICIO) + pd.to_timedelta(serie.semana * 7, unit="D")).dt.strftime("%Y-%m-%d")
    serie[["ibge", "semana", "novas_d1", "novas_comp"]].to_csv(raiz / "dados/processados/microdados_serie_semanal.csv", index=False)
    print(f"série semanal: {serie.ibge.nunique()} municípios, {serie.semana.nunique()} semanas; "
          f"pessoas 1ª dose {serie.novas_d1.sum():,}, completo {serie.novas_comp.sum():,}; "
          f"doses diárias: {len(dia)} dias, {int(dia.to_numpy().sum()):,} doses")


def agregar(saida: Path, raiz: Path):
    d, log = carregar(saida)
    m, de6 = de6_para_ibge(raiz)

    fluxo = d.groupby(["res_ibge", "est_ibge", "classe"], observed=True).size().rename("doses").reset_index()
    fluxo.to_csv(raiz / "dados/processados/microdados_doses_res_aplic.csv", index=False)

    def por(col):
        t = d[d[col].isin(de6)].groupby([col, "classe"], observed=True).size().unstack(fill_value=0)
        t.index = t.index.map(de6)
        return t

    res, apl = por("res_ibge"), por("est_ibge")
    out = m.set_index("ibge")[["municipio", "pop2022"]]
    for nome, t in (("res", res), ("apl", apl)):
        for k in ("D1", "D2", "DU", "REF"):
            out[f"{k.lower()}_{nome}"] = t.get(k, pd.Series(dtype=int)).reindex(out.index).fillna(0)
        out[f"cob_d1_{nome}"] = (out[f"d1_{nome}"] + out[f"du_{nome}"]) / out.pop2022
        out[f"cob_comp_{nome}"] = (out[f"d2_{nome}"] + out[f"du_{nome}"]) / out.pop2022
    tot_apl = apl.sum(axis=1).reindex(out.index).fillna(0)
    tot_res = res.sum(axis=1).reindex(out.index).fillna(0)
    out["saldo_importacao"] = (tot_apl - tot_res) / tot_res  # >0: aplica mais do que seus residentes recebem
    mesma = d[(d.res_ibge == d.est_ibge) & d.res_ibge.isin(de6)].groupby("res_ibge").size()
    mesma.index = mesma.index.map(de6)
    out["pct_doses_residentes_no_proprio_mun"] = (mesma.reindex(out.index) / tot_res).astype(float)

    # Abandono individual: pessoas com D1 e sem nenhuma D2. A pessoa é atribuída ao município de
    # residência informado na D1 (ou na D2, se não houver D1 registrada).
    p = d[d.classe.isin(["D1", "D2"])].copy()
    p["d1"], p["d2"] = p.classe == "D1", p.classe == "D2"
    p = p.sort_values("d1", ascending=False)  # linha da D1 primeiro → 'first' pega a residência da D1
    pessoa = p.groupby("paciente_id").agg(res=("res_ibge", "first"), tem_d1=("d1", "max"), tem_d2=("d2", "max"))
    pessoa = pessoa[pessoa.res.isin(de6)]
    ind = pessoa[pessoa.tem_d1].groupby("res").agg(pessoas_d1=("tem_d2", "size"), com_d2=("tem_d2", "sum"))
    ind.index = ind.index.map(de6)
    out = out.join(ind)
    out["abandono_individual"] = 1 - out.com_d2 / out.pessoas_d1
    sem_d1 = pessoa[~pessoa.tem_d1].groupby("res").size()
    sem_d1.index = sem_d1.index.map(de6)
    out["d2_sem_d1_registrada"] = sem_d1.reindex(out.index).fillna(0)

    out.index.name = "ibge"
    out.reset_index().to_csv(raiz / "dados/processados/microdados_municipal.csv", index=False, float_format="%.6g")
    log += [f"- Municípios do CE com dados: {out.d1_res.gt(0).sum()} (residência), {out.d1_apl.gt(0).sum()} (aplicação)",
            f"- Doses de residentes do CE aplicadas fora do CE: {(d.res_ibge.isin(de6) & ~d.est_ibge.isin(de6)).sum():,}",
            f"- Doses aplicadas no CE em residentes de fora: {(~d.res_ibge.isin(de6) & d.est_ibge.isin(de6)).sum():,}",
            f"- Municípios > 100% (D1+DU, Censo): residência {(out.cob_d1_res > 1).sum()}, aplicação {(out.cob_d1_apl > 1).sum()}",
            f"- Abandono individual (mediana): {out.abandono_individual.median():.3f}"]
    (raiz / "relatorios/microdados_validacao.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["filtrar", "agregar", "series"])
    ap.add_argument("arquivos", nargs="*", type=Path)
    ap.add_argument("--saida", type=Path, default=Path("dados/brutos/microdados_CE"))
    ap.add_argument("--raiz", type=Path, default=Path("."))
    a = ap.parse_args()
    if a.etapa == "filtrar":
        if not a.arquivos:
            raise SystemExit("Informe os arquivos baixados.")
        filtrar(a.arquivos, a.saida)
    elif a.etapa == "series":
        series(a.saida, a.raiz)
    else:
        agregar(a.saida, a.raiz)


if __name__ == "__main__":
    main()
