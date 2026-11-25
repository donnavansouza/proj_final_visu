"""
Coleta das bases pendentes do projeto "Quem ficou para trás?" (Ceará).

Rode no seu computador (o ambiente do Claude não alcança IBGE nem DATASUS):

    pip install requests pandas dbfread
    python pipeline/coleta_ibge_cnes.py            # faz tudo
    python pipeline/coleta_ibge_cnes.py sidra      # só as tabelas do Censo 2022
    python pipeline/coleta_ibge_cnes.py cnes       # só CNES (estabelecimentos e equipes)

Rode da raiz do projeto. Saída: dados/brutos/ibge/ (SIDRA), dados/brutos/cnes/ (CNES) e
dados/brutos/log_coleta.txt.
"""
import ftplib, io, json, os, sys, time, hashlib, datetime as dt
import requests
import pandas as pd

OUT = os.path.join("dados", "brutos", "ibge")        # SIDRA
OUT_CNES = os.path.join("dados", "brutos", "cnes")   # CNES
os.makedirs(OUT, exist_ok=True)
os.makedirs(OUT_CNES, exist_ok=True)
LOG = open(os.path.join("dados", "brutos", "log_coleta.txt"), "a", encoding="utf-8")


def log(msg):
    linha = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(linha)
    LOG.write(linha + "\n")
    LOG.flush()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 1) SIDRA / IBGE — API de agregados v3
# ---------------------------------------------------------------------------
API = "https://servicodados.ibge.gov.br/api/v3/agregados"
# tabela -> palavra-chave da classificação que deve vir ABERTA (None = só totais)
SIDRA = {
    "10295": None,                       # rendimento per capita (as variáveis importam)
    "10061": "instru",                   # nível de instrução, 18+
    "9537": "religi",                    # religião, 10+
    "9942": "internet",                  # conexão domiciliar à internet
    "9923": "situa",                     # situação do domicílio (urbana/rural)
}


def get_json(url, tentativas=4):
    for i in range(tentativas):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            log(f"  falha ({e}); tentativa {i + 1}/{tentativas}")
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"não consegui baixar {url}")


def categoria_total(classif):
    cats = classif["categorias"]
    for c in cats:
        if c["nome"].strip().lower().startswith("total"):
            return c["id"]
    niv0 = [c for c in cats if c.get("nivel", 0) in (0, None)]
    return (niv0 or cats)[0]["id"]


def coleta_sidra():
    for tab, chave in SIDRA.items():
        log(f"SIDRA {tab}: lendo metadados")
        meta = get_json(f"{API}/{tab}/metadados")
        with open(os.path.join(OUT, f"sidra_{tab}_metadados.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        partes = []
        for c in meta.get("classificacoes", []):
            if chave and chave in c["nome"].lower():
                partes.append(f"{c['id']}[all]")
                log(f"  aberta: {c['nome']} ({len(c['categorias'])} categorias)")
            else:
                partes.append(f"{c['id']}[{categoria_total(c)}]")
        classif = "|".join(partes)
        url = (f"{API}/{tab}/periodos/2022/variaveis/all"
               f"?localidades=N6[N3[23]]" + (f"&classificacao={classif}" if classif else ""))
        log(f"  baixando dados: {url}")
        dados = get_json(url)
        linhas = []
        for var in dados:
            for res in var["resultados"]:
                cats = {}
                for cl in res["classificacoes"]:
                    (cid, cnome), = cl["categoria"].items()
                    cats[cl["nome"]] = cnome
                for s in res["series"]:
                    for periodo, valor in s["serie"].items():
                        linhas.append({
                            "tabela": tab, "variavel_id": var["id"], "variavel": var["variavel"],
                            "unidade": var.get("unidade"), "ibge": s["localidade"]["id"],
                            "municipio": s["localidade"]["nome"], "periodo": periodo,
                            **{f"cat_{k}": v for k, v in cats.items()}, "valor": valor,
                        })
        df = pd.DataFrame(linhas)
        path = os.path.join(OUT, f"sidra_{tab}.csv")
        df.to_csv(path, index=False, encoding="utf-8")
        log(f"  OK {path}: {len(df)} linhas, {df['ibge'].nunique() if len(df) else 0} municípios")


# ---------------------------------------------------------------------------
# 2) CNES — arquivos brutos do FTP do DATASUS (ST = estabelecimentos, EP = equipes)
# ---------------------------------------------------------------------------
FTP_HOST = "ftp.datasus.gov.br"
CNES_DIR = "/dissemin/publicos/CNES/200508_/Dados"
CNES_ARQS = [("ST", "STCE2012"), ("ST", "STCE2112"), ("EP", "EPCE2012"), ("EP", "EPCE2112")]


# --- Leitor de .dbc em Python puro (dispensa pyreaddbc, que exige compilador C no Windows).
# DBC do DATASUS = cabeçalho DBF + 4 bytes de CRC + corpo comprimido no formato PKWare DCL
# ("implode"). O descompressor abaixo é uma tradução direta do blast.c de Mark Adler.
_MAXBITS = 13
_LITLEN = bytes([
    11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
    9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
    7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
    8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
    44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
    44, 173])
_LENLEN = bytes([2, 35, 36, 53, 38, 23])
_DISTLEN = bytes([2, 20, 53, 230, 247, 151, 248])
_BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def _huffman(rep):
    comprimentos = []
    for b in rep:
        comprimentos += [b & 15] * ((b >> 4) + 1)
    count = [0] * (_MAXBITS + 1)
    for c in comprimentos:
        count[c] += 1
    offs = [0] * (_MAXBITS + 2)
    for i in range(1, _MAXBITS + 1):
        offs[i + 1] = offs[i] + count[i]
    simbolos = [0] * len(comprimentos)
    for s, c in enumerate(comprimentos):
        if c:
            simbolos[offs[c]] = s
            offs[c] += 1
    return count, simbolos


def _blast(dados: bytes) -> bytes:
    pos = bitbuf = bitcnt = 0

    def bits(n):
        nonlocal pos, bitbuf, bitcnt
        while bitcnt < n:
            bitbuf |= dados[pos] << bitcnt
            pos += 1
            bitcnt += 8
        v = bitbuf & ((1 << n) - 1)
        bitbuf >>= n
        bitcnt -= n
        return v

    def decode(h):
        count, simbolos = h
        code = first = index = 0
        for comp in range(1, _MAXBITS + 1):
            code |= bits(1) ^ 1  # códigos vêm invertidos
            n = count[comp]
            if code - first < n:
                return simbolos[index + code - first]
            index += n
            first = (first + n) << 1
            code <<= 1
        raise ValueError("código Huffman inválido no .dbc")

    litcode, lencode, distcode = _huffman(_LITLEN), _huffman(_LENLEN), _huffman(_DISTLEN)
    lit, dic = bits(8), bits(8)
    if lit > 1 or not 4 <= dic <= 6:
        raise ValueError("cabeçalho PKWare inválido no .dbc")
    out = bytearray()
    while True:
        if bits(1):
            s = decode(lencode)
            comp = _BASE[s] + bits(_EXTRA[s])
            if comp == 519:  # fim
                break
            s = 2 if comp == 2 else dic
            dist = (decode(distcode) << s) + bits(s) + 1
            if dist > len(out):
                raise ValueError("distância inválida no .dbc")
            ini = len(out) - dist
            for i in range(comp):  # pode sobrepor: copiar byte a byte
                out.append(out[ini + i])
        else:
            out.append(decode(litcode) if lit else bits(8))
    return bytes(out)


def dbc_para_dbf(path_dbc, path_dbf):
    raw = open(path_dbc, "rb").read()
    tam_cab = raw[8] | (raw[9] << 8)
    cab = bytearray(raw[:tam_cab])
    cab[-1] = 0x0D  # o DATASUS grava 0x00 no terminador do cabeçalho; o dbfread exige 0x0D
    with open(path_dbf, "wb") as f:
        f.write(cab)
        f.write(_blast(raw[tam_cab + 4:]))


def le_dbc(path_dbc):
    from dbfread import DBF
    path_dbf = path_dbc[:-4] + ".dbf"
    dbc_para_dbf(path_dbc, path_dbf)
    return pd.DataFrame(iter(DBF(path_dbf, encoding="iso-8859-1", char_decode_errors="replace")))


def coleta_cnes():
    raw = os.path.join(OUT_CNES, "cnes_bruto")
    os.makedirs(raw, exist_ok=True)
    ftp = ftplib.FTP(FTP_HOST, timeout=120)
    ftp.login()
    for sub, nome in CNES_ARQS:
        destino = os.path.join(raw, nome + ".dbc")
        remoto = f"{CNES_DIR}/{sub}/{nome}.dbc"
        log(f"CNES: baixando {remoto}")
        try:
            with open(destino, "wb") as f:
                ftp.retrbinary(f"RETR {remoto}", f.write)
        except ftplib.error_perm as e:
            log(f"  ERRO: {e}. Confira se o arquivo existe em ftp://{FTP_HOST}{CNES_DIR}/{sub}/")
            continue
        log(f"  {os.path.getsize(destino):,} bytes, sha256 {sha256(destino)}")
        df = le_dbc(destino)
        df.columns = [c.upper() for c in df.columns]
        df.to_csv(os.path.join(OUT_CNES, f"cnes_{nome}.csv"), index=False, encoding="utf-8")
        log(f"  OK cnes_{nome}.csv: {len(df)} linhas, colunas: {', '.join(df.columns[:25])}...")
        # resumos para conferência rápida
        if sub == "ST" and "TP_UNID" in df:
            df.groupby(["CODUFMUN", "TP_UNID"]).size().rename("n").reset_index() \
              .to_csv(os.path.join(OUT_CNES, f"resumo_{nome}_tipo_unidade.csv"), index=False)
        if sub == "EP":
            col = next((c for c in ["TIPO_EQP", "TP_EQUIPE", "TIPO_EQUIPE"] if c in df), None)
            if col:
                df.groupby(["CODUFMUN", col]).size().rename("n").reset_index() \
                  .to_csv(os.path.join(OUT_CNES, f"resumo_{nome}_tipo_equipe.csv"), index=False)
    ftp.quit()


if __name__ == "__main__":
    etapas = sys.argv[1:] or ["sidra", "cnes"]
    if "sidra" in etapas:
        try:
            coleta_sidra()
        except Exception as e:  # noqa: BLE001
            log(f"SIDRA interrompido: {e}")
    if "cnes" in etapas:
        try:
            coleta_cnes()
        except Exception as e:  # noqa: BLE001
            log(f"CNES interrompido: {e}")
    log("Fim.")
