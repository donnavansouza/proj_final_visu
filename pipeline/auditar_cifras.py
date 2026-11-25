"""Auditoria das cifras do site contra relatorios/verificacoes_finais.md.

Lê os JSONs do site (json/) e o relatório de verificações, extrai de cada um o mesmo número
e compara (na precisão em que o site exibe). Grava relatorios/auditoria_cifras.md.

Status:  IGUAL   — mesmo valor nas duas fontes
         DIFERE  — valores diferentes (o relatório explica o motivo)
         NOVO    — número do site que não existe nas verificações (calculado na mesma base)
Uso:  python pipeline/auditar_cifras.py --raiz .
"""
import argparse
import json
import re
import sys
from pathlib import Path


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=Path("."), type=Path)
    raiz = ap.parse_args().raiz
    J = {n: json.loads((raiz / f"json/{n}.json").read_text(encoding="utf-8"))
         for n in ["cap1", "cap2", "cap3", "cap4", "cap5", "cap7"]}
    vf = (raiz / "relatorios/verificacoes_finais.md").read_text(encoding="utf-8")

    def busca(padrao, grupo=1, conv=float):
        m = re.search(padrao, vf, flags=re.M)
        if not m:
            raise SystemExit(f"padrão não encontrado em verificacoes_finais.md: {padrao}")
        return conv(m.group(grupo).replace(",", ""))

    linha_tab = lambda nome: re.search(rf"^\| {re.escape(nome)} \|(.+)$", vf, flags=re.M).group(1).split("|")
    pct = lambda s: float(s.strip().rstrip("%")) / 100
    fz, ita = linha_tab("Fortaleza"), linha_tab("Itaitinga")  # tabela da seção 3 (a última ocorrência é a da RMF)
    fz = re.findall(r"^\| Fortaleza \|(.+)$", vf, flags=re.M)[-1].split("|")
    ita = re.findall(r"^\| Itaitinga \|(.+)$", vf, flags=re.M)[-1].split("|")
    mapa = {m["id"]: m for m in J["cap7"]["municipios"]}
    t13 = {t["nome"]: t for t in J["cap4"]["treze"]}

    # (onde aparece, descrição, valor no site, valor nas verificações ou None, casas p/ comparar, formato)
    itens = [
        ("Cap. 3", "Municípios > 100% — registros ÷ Censo (estado b)", J["cap3"]["contagens"]["b"], busca(r"Por doses: \*\*(\d+)\*\*"), 0, "{:.0f}"),
        ("Cap. 3", "Municípios > 100% — pessoas ÷ Censo (estado c)", J["cap3"]["contagens"]["c"], busca(r"Por pessoas distintas: \*\*(\d+)\*\*"), 0, "{:.0f}"),
        ("Cap. 3", "Acima de 100% com os dois denominadores", J["cap3"]["contagens"]["robusto"], busca(r"com os dois denominadores: \*\*(\d+)\*\*"), 0, "{:.0f}"),
        ("Cap. 3", "Municípios > 100% — registros ÷ estimativa 2021 (estado a)", J["cap3"]["contagens"]["a"], None, 0, "{:.0f}"),
        ("Cap. 3", "Excesso de pessoas acima da população", J["cap3"]["excesso"]["pessoas"], busca(r"soma nos > 100%: ([\d,]+) pessoas"), 0, "{:,.0f}"),
        ("Cap. 3", "Excesso como % da população", J["cap3"]["excesso"]["pct_pop"], busca(r"pessoas \(([\d.]+)% da população") / 100, 4, "{:.2%}"),
        ("Cap. 3", "Itaitinga — 1ª dose, pessoas ÷ Censo", J["cap3"]["destaques"]["itaitinga"]["c"], pct(ita[4]), 3, "{:.1%}"),
        ("Cap. 3", "Fortaleza — 1ª dose, pessoas ÷ Censo", J["cap3"]["destaques"]["fortaleza"]["c"], pct(fz[4]), 3, "{:.1%}"),
        ("Cap. 2", "Fortaleza — esquema completo (pessoas)", J["cap2"]["fortaleza"]["comp"], pct(fz[3]), 3, "{:.1%}"),
        ("Cap. 2", "Fortaleza — abandono individual", J["cap2"]["fortaleza"]["abandono"], pct(fz[5]), 3, "{:.1%}"),
        ("Cap. 4", "Decomposição: parte da 1ª dose", J["cap4"]["decomp"]["pct_d1"], busca(r"No conjunto dos 13: (\d+)% da distância") / 100, 2, "{:.0%}"),
        ("Cap. 4", "Decomposição: parte do abandono", J["cap4"]["decomp"]["pct_aband"], busca(r"vem da 1ª dose e (\d+)% do abandono") / 100, 2, "{:.0%}"),
        ("Cap. 4", "Perfil 'os dois problemas'", J["cap4"]["perfis"]["dois"], busca(r"'os dois': (\d+)"), 0, "{:.0f}"),
        ("Cap. 4", "Perfil 'só começaram atrás'", J["cap4"]["perfis"]["atras"], busca(r"'começou atrás': (\d+)"), 0, "{:.0f}"),
        ("Cap. 4", "Perfil 'só não voltaram'", J["cap4"]["perfis"]["naovoltou"], busca(r"'não voltou': (\d+)"), 0, "{:.0f}"),
        ("Cap. 4", "Mediana 1ª dose (pessoas) — os 13", J["cap4"]["grupos"]["baixo_d1"], busca(r"^\| 1ª dose final \(pessoas\) \| ([\d.]+)"), 3, "{:.1%}"),
        ("Cap. 4", "Mediana 1ª dose (pessoas) — demais", J["cap4"]["ref"]["d1"], busca(r"^\| 1ª dose final \(pessoas\) \| [\d.]+ \| ([\d.]+)"), 3, "{:.1%}"),
        ("Cap. 4", "Mediana abandono — os 13", J["cap4"]["grupos"]["baixo_aband"], busca(r"^\| Abandono individual \| ([\d.]+) \|"), 3, "{:.1%}"),
        ("Cap. 4", "Mediana abandono — demais", J["cap4"]["ref"]["abandono"], busca(r"^\| Abandono individual \| [\d.]+ \| ([\d.]+) \|"), 3, "{:.1%}"),
        ("Cap. 4", "I de Moran — esquema completo (pessoas)", J["cap4"]["moran"]["cobertura"], busca(r"^\| Esquema completo final \(pessoas/Censo\) \| ([-+\d.]+)"), 3, "{:+.3f}"),
        ("Cap. 4", "I de Moran — voto em Bolsonaro 2018", J["cap4"]["moran"]["voto"], busca(r"^\| Referência: voto Bolsonaro 2018 \| ([-+\d.]+)"), 3, "{:+.3f}"),
        ("Cap. 4", "I de Moran — renda mediana", J["cap4"]["moran"]["renda"], busca(r"^\| Referência: renda mediana 2022 \| ([-+\d.]+)"), 3, "{:+.3f}"),
        ("Cap. 4", "Nova Olinda — abandono individual", t13["Nova Olinda"]["abandono"], busca(r"^\| Nova Olinda \| [\d.]+% \| \d+ª menor \| ([\d.]+)%") / 100, 3, "{:.1%}"),
        ("Cap. 4", "Aurora — abandono individual", t13["Aurora"]["abandono"], busca(r"^\| Aurora \| [\d.]+% \| \d+ª menor \| ([\d.]+)%") / 100, 3, "{:.1%}"),
        ("Cap. 1", "Doses aplicadas a residentes do CE", J["cap1"]["doses_total"], None, 0, "{:,.0f}"),
        ("Cap. 1", "Correlação de postos dez/21 × final", J["cap1"]["marcos"]["rho_dez21_fim"], None, 2, "{:.2f}"),
        ("Cap. 1", "Largura da faixa P10–P90 em dez/21 (pontos)", J["cap1"]["marcos"]["largura_dez21"], None, 2, "{:.0%}"),
        ("Cap. 2", "Rede de saúde: ρ parcial (porte e erro de pop.)", J["cap2"]["suspeitos"][3]["stats"]["rho_parcial"], None, 2, "{:+.2f}"),
        ("Cap. 5", "Reforço: razão entre o décimo de cima e o de baixo", J["cap5"]["razao_p90_p10"], None, 2, "{:.2f}"),
        ("Cap. 5", "R² máximo das variáveis medidas", J["cap5"]["r2_max"], None, 2, "{:.0%}"),
        ("Cap. 7", "Nova Olinda — esquema completo (pessoas)", mapa["2309201"]["comp"], None, 3, "{:.1%}"),
    ]
    L = ["# Auditoria das cifras do site", "",
         "Gerado por `pipeline/auditar_cifras.py`. Compara o que o site exibe (JSONs em `json/`) com "
         "`relatorios/verificacoes_finais.md`. NOVO = número que só existe no site, calculado na mesma base "
         "(pessoas, residência, Censo 2022).", "",
         "| Onde | Cifra | Site | Verificações | Status |", "|---|---|---|---|---|"]
    cont = {"IGUAL": 0, "DIFERE": 0, "NOVO": 0}
    for onde, desc, site, ref, casas, f in itens:
        if ref is None:
            st = "NOVO"
        else:
            st = "IGUAL" if round(float(site), casas + (2 if "%" in f else 0)) == round(float(ref), casas + (2 if "%" in f else 0)) \
                or f.format(site) == f.format(ref) else "DIFERE"
        cont[st] += 1
        L.append(f"| {onde} | {desc} | {f.format(site)} | {'—' if ref is None else f.format(ref)} | {st} |")
    L += ["", f"**Resumo:** {cont['IGUAL']} iguais, {cont['DIFERE']} diferentes, {cont['NOVO']} novos.", "",
          "## Diferenças conhecidas em relação ao roteiro original (não às verificações)", "",
          "- Doses: o roteiro dizia 24,7 milhões (base `processed_CE`); o site usa os microdados, "
          "doses a residentes do CE no mesmo período.",
          "- Correlação dez/21 × final: o roteiro dizia 0,92 (doses); com pessoas é a do quadro acima.",
          "- Contador do capítulo 3: o roteiro dizia 60 → 41 → 14; o estado (a) tem o valor do quadro, "
          "e o 14 virou um passo próprio (os que seguem acima de 100% com qualquer denominador).",
          "- R² máximo: o roteiro dizia ~20%; o valor calculado está no quadro.",
          "- Os 13 seguem o critério das verificações (registros ÷ Censo); contando pessoas, "
          f"{J['cap4']['n_pessoas_abaixo_70']} municípios ficam abaixo de 70% (nota no próprio capítulo)."]
    (raiz / "relatorios/auditoria_cifras.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    if cont["DIFERE"]:
        raise SystemExit(f"{cont['DIFERE']} cifra(s) diferem das verificações")


if __name__ == "__main__":
    main()
