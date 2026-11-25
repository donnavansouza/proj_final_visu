"""Refaz, na ordem, tudo o que dá para refazer com o que está no repositório.

Uso (da raiz do projeto):  python pipeline/rodar_tudo.py

Ficam de fora as etapas que dependem de arquivos de fora do repositório:
  coleta_ibge_cnes.py   (baixa da internet; o resultado já está em dados/brutos/ibge e cnes)
  base_municipal.py     (precisa dos óbitos cases_*.csv.gz; ver docs/06)
  microdados filtrar    (precisa dos 5 CSVs originais do OpenDataSUS, ~13 GB)
As etapas de microdados (agregar e series) só rodam se dados/brutos/microdados_CE/ existir
no seu computador (ele não vai para o GitHub; ver docs/06).
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MICRO = RAIZ / "dados/brutos/microdados_CE"

ETAPAS = [
    ("Eleições por município (TSE)", ["tse_municipal.py"]),
    ("Rede de saúde e Censo (CNES + IBGE)", ["aps_censo.py"]),
    ("Junta tudo e testa a hipótese política", ["analise_politica.py"]),
    ("Testa as demais hipóteses", ["analise_eixos.py"]),
    ("Microdados: totais por município", ["microdados_vacinacao.py", "agregar"]),
    ("Microdados: séries semanais", ["microdados_vacinacao.py", "series"]),
    ("Verificações finais", ["verificacoes_finais.py"]),
    ("Gera os JSONs do site", ["preparar_site.py"]),
    ("Confere os números do site", ["auditar_cifras.py"]),
]

sys.stdout.reconfigure(encoding="utf-8")  # acentos no console do Windows

for i, (nome, cmd) in enumerate(ETAPAS, 1):
    if cmd[0] == "microdados_vacinacao.py" and not MICRO.exists():
        print(f"[{i}/{len(ETAPAS)}] {nome}: PULADA (sem {MICRO.relative_to(RAIZ)}; usa os CSVs já em dados/processados)")
        continue
    print(f"[{i}/{len(ETAPAS)}] {nome} ...", flush=True)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", str(RAIZ / "pipeline" / cmd[0]), *cmd[1:]],
                       cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-4000:], sep="\n")
        sys.exit(f"Falhou na etapa {i}: {nome}")
print("Pronto. Site atualizado em json/; relatórios em relatorios/.")
