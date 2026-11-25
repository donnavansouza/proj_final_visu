// Capítulo 4 — Quem ficou para trás de verdade.
// Um SVG fixo com quatro vistas: dispersão → mapa (os pontos voam até cada município) → os 13 →
// funil 1ª dose → esquema completo por perfil. Depois, três mapas lado a lado com o I de Moran.
/* global d3 */
import { COR, DUR, EASE, fmt, reduzMovimento, scrolly, tooltip, aoRedimensionar } from "./util.js";

// perfis (cores validadas: luminância 0,11 / 0,20 / 0,43 — distintas também em cinza) + formas
export const PERFIS = {
  dois: { cor: "#2A5FA0", forma: d3.symbolCircle, rot: "Os dois problemas" },
  atras: { cor: "#C0633A", forma: d3.symbolSquare, rot: "Só começaram atrás" },
  naovoltou: { cor: "#DDA73B", forma: d3.symbolDiamond, rot: "Só não voltaram" },
};
const ORDEM_PERFIS = ["dois", "atras", "naovoltou"];

export function initCap4(c4, c2, geo, municipios) {
  vistaPrincipal(c4, c2, geo, municipios);
  tresMapas(c4, geo, municipios);
}

function vistaPrincipal(c4, c2, geo, municipios) {
  const fig = document.getElementById("g-atrasados");
  const box = fig.querySelector(".atr-svg");
  const nome = new Map(municipios.map((m) => [m.id, m.nome]));
  const treze = new Map(c4.treze.map((t) => [t.id, t]));
  const pts = c2.municipios; // y = esquema completo (pessoas), habito = influenza 2019 (último suspeito)
  const feats = geo.features;

  const svg = d3.select(box).append("svg").attr("role", "img").attr("aria-labelledby", "g-atr-titulo g-atr-desc");
  svg.append("title").attr("id", "g-atr-titulo").text("Os 13 municípios que ficaram para trás");
  const desc = svg.append("desc").attr("id", "g-atr-desc");
  const gEixos = svg.append("g").attr("class", "eixos-atr");
  const gX = gEixos.append("g").attr("class", "eixo eixo-x");
  const gY = gEixos.append("g").attr("class", "eixo eixo-y");
  const gMapa = svg.append("g").attr("class", "mapa-atr").style("opacity", 0);
  const gPts = svg.append("g").attr("class", "pontos");
  const gSimb = svg.append("g").attr("class", "simbolos").style("opacity", 0);
  const gFunil = svg.append("g").attr("class", "funil").style("opacity", 0).style("pointer-events", "none");

  // legenda dos perfis (HTML; sempre presente, a cor nunca é o único código)
  const leg = d3.select(fig).select(".legenda-perfis");
  ORDEM_PERFIS.forEach((k) => {
    const it = leg.append("span").attr("class", "leg-item");
    it.append("svg").attr("width", 14).attr("height", 14).append("path")
      .attr("transform", "translate(7,7)").attr("d", d3.symbol(PERFIS[k].forma, 90)())
      .attr("fill", PERFIS[k].cor).attr("stroke", COR.tinta).attr("stroke-width", 0.8);
    it.append("span").text(`${PERFIS[k].rot} (${c4.perfis[k]})`);
  });

  let W, H, proj, path, posDisp, posMapa, vista = "disp";

  function layout() {
    W = box.clientWidth;
    H = Math.max(320, Math.min(560, box.clientHeight || 480));
    if (window.innerWidth <= 860) H = Math.max(300, Math.min(H, window.innerHeight * 0.5)); // texto rola por baixo
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    // dispersão (mesmo desenho do cap. 2, X = influenza 2019)
    const m = { t: 20, r: 18, b: 40, l: 48 };
    const x = d3.scaleLinear().domain(d3.extent(pts, (d) => d.habito)).nice().range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([d3.min(pts, (d) => d.y) - 0.02, Math.max(1.02, d3.max(pts, (d) => d.y))]).nice()
      .range([H - m.b, m.t]);
    gX.attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(5).tickFormat((v) => fmt.pct(v)).tickSizeOuter(0));
    gY.attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(8))
      .call((g) => g.select(".domain").remove());
    posDisp = new Map(pts.map((d) => [d.id, [x(d.habito), y(d.y)]]));
    // mapa
    proj = d3.geoMercator().fitExtent([[10, 10], [W - 10, H - 10]], geo);
    path = d3.geoPath(proj);
    posMapa = new Map(feats.map((f) => [f.id, path.centroid(f)]));
    gMapa.selectAll("path").data(feats, (f) => f.id).join("path").attr("d", path)
      .on("pointermove", (ev, f) => tooltip.mostrar(tt(f.id), ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder());
    gSimb.selectAll("path").data(c4.treze, (d) => d.id).join("path")
      .attr("transform", (d) => `translate(${posMapa.get(d.id)})`)
      .attr("d", (d) => d3.symbol(PERFIS[d.perfil].forma, 110)())
      .attr("fill", (d) => PERFIS[d.perfil].cor).attr("stroke", COR.tinta).attr("stroke-width", 1);
    funil();
    aplicar(vista, false);
  }

  function tt(id) {
    const t = treze.get(id);
    const d = pts.find((p) => p.id === id);
    return `<strong>${nome.get(id)}</strong>
      <div class="tt-linha">Esquema completo <b>${fmt.pct1(d.y)}</b></div>
      ${t ? `<div class="tt-linha">1ª dose <b>${fmt.pct1(t.d1)}</b></div>
             <div class="tt-linha">Abandono <b>${fmt.pct1(t.abandono)}</b></div>
             <div class="tt-nota">${PERFIS[t.perfil].rot}</div>` : ""}`;
  }

  // ---------- funil: 1ª dose → esquema completo, por perfil ----------
  function funil() {
    gFunil.selectAll("*").remove();
    const estreito = W < 520;
    const m = { t: 52, r: estreito ? 44 : 92, b: 34, l: estreito ? 112 : 150 };
    const linhas = [];
    ORDEM_PERFIS.forEach((k) => {
      const grupo = c4.treze.filter((t) => t.perfil === k).sort((a, b) => a.comp - b.comp);
      if (!grupo.length) return;
      linhas.push({ cab: true, k });
      grupo.forEach((t) => linhas.push({ t, k }));
    });
    const alt = Math.min(28, (H - m.t - m.b) / linhas.length);
    const minimo = Math.floor(d3.min(c4.treze, (t) => t.comp) * 10) / 10;   // Nova Olinda fica abaixo de 50%
    const x = d3.scaleLinear().domain([minimo, 1]).range([m.l, W - m.r]);
    gFunil.append("g").attr("class", "eixo eixo-x").attr("transform", `translate(0,${m.t - 8})`)
      .call(d3.axisTop(x).tickValues(d3.range(minimo, 1.0001, estreito ? 0.2 : 0.1)).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(4))
      .call((g) => g.select(".domain").remove());
    // referências: medianas dos demais municípios (rótulos em lados opostos para não colidirem)
    // em tela estreita, os dois rótulos ficam em linhas diferentes, ancorados à esquerda da linha
    [["comp", "completo, demais", "end", -4, 0], ["d1", "1ª dose, demais", estreito ? "end" : "start", estreito ? -4 : 4, estreito ? 14 : 0]]
      .forEach(([k, rot, ancora, dx, dy]) => {
        const xx = x(c4.ref[k]);
        gFunil.append("line").attr("class", "ref-funil").attr("x1", xx).attr("x2", xx).attr("y1", m.t).attr("y2", m.t + alt * linhas.length + dy);
        gFunil.append("text").attr("class", "rot-ref").attr("x", xx + dx).attr("y", m.t + alt * linhas.length + 14 + dy)
          .attr("text-anchor", ancora).text(`${rot}: ${fmt.pct(c4.ref[k])}`);
      });
    const g = gFunil.selectAll("g.lin").data(linhas).join("g").attr("class", "lin")
      .attr("transform", (_, i) => `translate(0,${m.t + i * alt + alt / 2})`);
    g.filter((d) => d.cab).append("text").attr("class", "cab-perfil").attr("x", 0).attr("dy", "0.32em")
      .text((d) => PERFIS[d.k].rot);
    const r = g.filter((d) => !d.cab);
    r.append("text").attr("class", "rot-mun").attr("x", m.l - 10).attr("text-anchor", "end").attr("dy", "0.32em")
      .text((d) => d.t.nome);
    r.append("line").attr("class", "perda").attr("x1", (d) => x(d.t.comp)).attr("x2", (d) => x(d.t.d1));
    r.append("path").attr("transform", (d) => `translate(${x(d.t.d1)},0)`).attr("d", (d) => d3.symbol(PERFIS[d.k].forma, 70)())
      .attr("fill", COR.fundo).attr("stroke", (d) => PERFIS[d.k].cor).attr("stroke-width", 2);
    r.append("path").attr("transform", (d) => `translate(${x(d.t.comp)},0)`).attr("d", (d) => d3.symbol(PERFIS[d.k].forma, 80)())
      .attr("fill", (d) => PERFIS[d.k].cor).attr("stroke", COR.tinta).attr("stroke-width", 0.8);
    r.append("text").attr("class", "rot-aband").attr("x", W - m.r + 8).attr("dy", "0.32em")
      .text((d) => (estreito ? fmt.pct(d.t.abandono) : `abandono ${fmt.pct(d.t.abandono)}`));
    if (estreito) gFunil.append("text").attr("class", "rot-ref").attr("x", W - m.r + 8).attr("y", m.t - 24).text("aband.");
    // chave de leitura no topo
    const k = gFunil.append("g").attr("class", "chave-funil").attr("transform", `translate(${estreito ? 0 : m.l},${12})`);
    k.append("text").attr("class", "rot-ref").text(estreito ? "○ 1ª dose  ● completo  — quem não voltou"
      : "○ 1ª dose   ● esquema completo   — a linha é quem não voltou");
  }

  function aplicar(v, animar = true) {
    vista = v;
    const dur = animar && !reduzMovimento ? DUR : 0;
    const t = (s) => (dur ? s.transition().duration(dur).ease(EASE) : s);
    const emMapa = v === "mapa" || v === "treze";
    t(gEixos).style("opacity", v === "disp" ? 1 : 0);
    t(gMapa).style("opacity", emMapa ? 1 : 0);
    gMapa.style("pointer-events", emMapa ? null : "none");
    t(gMapa.selectAll("path")).attr("fill", (f) => (v === "treze" && treze.has(f.id) ? PERFIS[treze.get(f.id).perfil].cor : "#E6DBC4"))
      .attr("fill-opacity", (f) => (v === "treze" && treze.has(f.id) ? 0.45 : 1));
    t(gSimb).style("opacity", v === "treze" ? 1 : 0);
    t(gFunil).style("opacity", v === "funil" ? 1 : 0);
    gFunil.style("pointer-events", v === "funil" ? null : "none");

    // a transição-assinatura: os pontos da dispersão voam até a posição de cada município
    const sel = gPts.selectAll("circle").data(pts, (d) => d.id).join((e) => e.append("circle")
      .attr("fill", COR.azul).attr("stroke", COR.fundo).attr("stroke-width", 1.2)
      .attr("cx", (d) => posDisp.get(d.id)[0]).attr("cy", (d) => posDisp.get(d.id)[1]).attr("r", 4.5)
      .on("pointermove", (ev, d) => tooltip.mostrar(tt(d.id), ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder()));
    const destino = v === "disp" ? posDisp : posMapa;
    const atraso = (d) => (dur ? (posMapa.get(d.id)[0] / W) * 500 : 0);
    (dur ? sel.transition().duration(dur + 150).ease(EASE).delay(atraso) : sel)
      .attr("cx", (d) => destino.get(d.id)[0]).attr("cy", (d) => destino.get(d.id)[1])
      .attr("r", v === "disp" ? 4.5 : 2.6)
      .attr("fill-opacity", v === "disp" ? 0.78 : v === "mapa" ? 0.9 : 0)
      .attr("stroke-opacity", v === "disp" || v === "mapa" ? 1 : 0);
    gPts.style("pointer-events", v === "disp" ? null : "none");

    desc.text({
      disp: "Dispersão dos 184 municípios: esquema completo contra cobertura da gripe em 2019.",
      mapa: "Os mesmos 184 municípios, agora na posição de cada um no mapa do Ceará.",
      treze: `Os 13 municípios com esquema completo abaixo de 70%, espalhados pelo estado, marcados por perfil.`,
      funil: "Para cada um dos 13: 1ª dose e esquema completo, por perfil, com as medianas dos demais municípios.",
    }[v]);
  }

  const passos = [...document.querySelectorAll("#cap4 .passo")].map((el) => el.dataset.vista);
  scrolly("#cap4 .passo", { onPasso: (i) => aplicar(passos[i]) });
  aoRedimensionar(layout).observe(box);
  layout();
}

// ---------- três mapas lado a lado com o I de Moran ----------
function tresMapas(c4, geo, municipios) {
  const fig = document.getElementById("g-moran");
  const nome = new Map(municipios.map((m) => [m.id, m.nome]));
  const vals = new Map(c4.mapas.map((m) => [m.id, m]));
  const paineis = [
    { k: "cobertura", tit: "Esquema completo", f: fmt.pct },
    { k: "voto", tit: "Voto em Bolsonaro, 2018", f: (v) => `${fmt.int(v)}%` },
    { k: "renda", tit: "Renda mediana, 2022", f: (v) => `R$ ${fmt.int(v)}` },
  ];
  const cards = d3.select(fig).selectAll("div.painel").data(paineis).join("div").attr("class", "painel");
  cards.append("p").attr("class", "painel-tit").text((p) => p.tit);
  cards.append("p").attr("class", "painel-moran").html((p) => `I de Moran <b>${fmt.rho(c4.moran[p.k])}</b>`);
  cards.each(function (p) {
    const card = d3.select(this);
    const vs = c4.mapas.map((m) => m[p.k]);
    // 7 classes por quantil, para comparar a FORMA da distribuição no espaço, não o nível
    const cor = d3.scaleQuantile().domain(vs).range(COR.cobertura);
    const svg = card.append("svg").attr("role", "img")
      .attr("aria-label", `${p.tit}: I de Moran ${fmt.rho(c4.moran[p.k])}`);
    const g = svg.append("g");
    const lg = card.append("div").attr("class", "painel-leg");
    lg.append("span").text(`${p.f(d3.min(vs))}`);
    lg.append("span").attr("class", "painel-rampa").style("background",
      `linear-gradient(90deg, ${COR.cobertura.join(",")})`);
    lg.append("span").text(`${p.f(d3.max(vs))}`);
    const desenhar = () => {
      const W = card.node().clientWidth;
      const H = W * 1.05;
      svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
      const path = d3.geoPath(d3.geoMercator().fitExtent([[4, 4], [W - 4, H - 4]], geo));
      g.selectAll("path").data(geo.features, (f) => f.id).join("path").attr("d", path)
        .attr("fill", (f) => cor(vals.get(f.id)[p.k]))
        .on("pointermove", (ev, f) => tooltip.mostrar(`<strong>${nome.get(f.id)}</strong>
          <div class="tt-linha">${p.tit} <b>${p.f(vals.get(f.id)[p.k])}</b></div>`, ev.clientX, ev.clientY))
        .on("pointerleave", () => tooltip.esconder());
    };
    aoRedimensionar(desenhar).observe(card.node());
    desenhar();
  });
}
