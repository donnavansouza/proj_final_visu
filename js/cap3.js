// Capítulo 3 — A reviravolta: a medida mentia. Mapa de 1ª dose que se corrige com a rolagem:
// (a) registros ÷ estimativa 2021 → (b) registros ÷ Censo 2022 → (c) pessoas ÷ Censo 2022.
// A cor tem teto em 100%; valores acima de 100% ganham contorno de alerta e aparecem reais no tooltip.
/* global d3 */
import { COR, DUR, EASE, fmt, reduzMovimento, scrolly, tooltip, clamp01, lerp, escalaCobertura, aoRedimensionar, PASSOS_COBERTURA } from "./util.js";

const ESTADOS = {
  a: "Registros de 1ª dose ÷ estimativa de 2021",
  b: "Registros de 1ª dose ÷ Censo 2022",
  c: "Pessoas com 1ª dose ÷ Censo 2022",
};

export function initCap3(geo, c3, municipios) {
  const fig = document.getElementById("g-mapa");
  const nome = new Map(municipios.map((m) => [m.id, m.nome]));
  const val = new Map(c3.municipios.map((m) => [m.id, m]));
  const cor = escalaCobertura();

  const svg = d3.select(fig.querySelector(".mapa-svg")).append("svg").attr("role", "img")
    .attr("aria-labelledby", "g-mapa-titulo g-mapa-desc");
  svg.append("title").attr("id", "g-mapa-titulo").text("Cobertura da 1ª dose por município do Ceará");
  const desc = svg.append("desc").attr("id", "g-mapa-desc");
  const defs = svg.append("defs");
  // textura a 45° (identidade secundária): município sensível ao denominador
  const pat = defs.append("pattern").attr("id", "hachura-sensivel").attr("patternUnits", "userSpaceOnUse")
    .attr("width", 5).attr("height", 5).attr("patternTransform", "rotate(45)");
  pat.append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 5)
    .attr("stroke", COR.tinta).attr("stroke-width", 1.4).attr("stroke-opacity", 0.75);

  const gMun = svg.append("g").attr("class", "municipios");
  const gSens = svg.append("g").attr("class", "sensivel");
  const gAlerta = svg.append("g").attr("class", "alertas");
  const gRot = svg.append("g").attr("class", "rotulos-mapa");

  const contador = fig.querySelector(".contador-num");
  const rotEstado = fig.querySelector(".estado-rotulo");
  legenda(fig.querySelector(".legenda-mapa"), cor);

  let path, dCache = new Map(), feats = geo.features;
  const estado = { de: "a", para: "a", t: 0, foco: [], robusto: false };

  // valor de um município no estado corrente (interpolado entre dois estados)
  const valor = (id) => { const m = val.get(id); return lerp(m[estado.de], m[estado.para], estado.t); };

  function layout() {
    const W = fig.querySelector(".mapa-svg").clientWidth;
    const H = Math.max(300, Math.min(W * 1.05, window.innerHeight * 0.62));
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    const proj = d3.geoMercator().fitExtent([[8, 8], [W - 8, H - 8]], geo);
    path = d3.geoPath(proj);
    dCache = new Map(feats.map((f) => [f.id, path(f)]));
    gMun.selectAll("path").data(feats, (f) => f.id).join((e) => e.append("path")
      .attr("tabindex", -1)
      .on("pointermove", (ev, f) => tooltip.mostrar(tt(f.id), ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder()))
      .attr("d", path);
    gSens.selectAll("path").data(feats.filter((f) => val.get(f.id).sensivel), (f) => f.id).join("path")
      .attr("d", path).attr("fill", "url(#hachura-sensivel)").attr("pointer-events", "none");
    desenhar(false);
  }

  function tt(id) {
    const m = val.get(id), v = valor(id);
    const alerta = (x) => (x > 1 ? ' <span class="alerta-icone" aria-label="acima de 100%">▲</span>' : "");
    return `<strong>${nome.get(id)}</strong>
      <div class="tt-linha">Agora: <b>${fmt.pct1(v)}</b>${alerta(v)}</div>
      <div class="tt-tabela">
        <span>÷ estimativa 2021</span><b>${fmt.pct1(m.a)}${alerta(m.a)}</b>
        <span>÷ Censo 2022</span><b>${fmt.pct1(m.b)}${alerta(m.b)}</b>
        <span>pessoas ÷ Censo</span><b>${fmt.pct1(m.c)}${alerta(m.c)}</b>
      </div>
      ${m.dup > 1.02 ? `<div class="tt-nota">${fmt.dec2(m.dup)} registros de 1ª dose por pessoa</div>` : ""}
      ${m.sensivel ? '<div class="tt-nota">Sensível ao denominador</div>' : ""}`;
  }

  function desenhar(animar = true) {
    const sel = gMun.selectAll("path");
    const t = animar && !reduzMovimento ? sel.transition().duration(DUR / 3).ease(EASE) : sel;
    t.attr("fill", (f) => cor(valor(f.id)));
    // alerta: contorno terracota em quem passa de 100% (no estado corrente)
    const acima = feats.filter((f) => valor(f.id) > 1);
    const dest = estado.robusto ? new Set(c3.municipios.filter((m) => m.robusto).map((m) => m.id)) : null;
    gAlerta.selectAll("path").data(acima, (f) => f.id).join(
      (e) => e.append("path").attr("d", (f) => dCache.get(f.id)).style("opacity", 0)
        .call((s) => (reduzMovimento ? s : s.transition().duration(DUR / 2)).style("opacity", 1)),
      (u) => u.attr("d", (f) => dCache.get(f.id)),
      (x) => (reduzMovimento ? x.remove() : x.transition().duration(DUR / 2).style("opacity", 0).remove()))
      .attr("class", (f) => (dest && !dest.has(f.id) ? "alerta apagado" : "alerta"));
    const n = acima.length;
    contador.textContent = fmt.int(n);
    contador.closest(".contador").setAttribute("aria-label", `${n} municípios acima de 100%`);
    const rot = estado.t < 0.5 ? ESTADOS[estado.de] : ESTADOS[estado.para];
    if (rotEstado.textContent !== rot) rotEstado.textContent = rot;
    desc.text(`${rot}. ${n} municípios acima de 100%. Cor com teto em 100%; contorno marca valores acima de 100%.`);
    rotular();
  }

  // rótulos dos municípios citados no texto, com linha de chamada
  function rotular() {
    const dados = estado.foco.map((id) => {
      const f = feats.find((g) => g.id === id);
      const [cx, cy] = path.centroid(f);
      return { id, cx, cy, txt: `${nome.get(id)}: ${fmt.pct(valor(id))}` };
    });
    const W = +svg.attr("width");
    const g = gRot.selectAll("g.rot").data(dados, (d) => d.id).join((e) => {
      const s = e.append("g").attr("class", "rot").style("opacity", 0);
      s.append("line");
      s.append("circle").attr("r", 3);
      s.append("text");
      s.transition().duration(reduzMovimento ? 0 : DUR / 2).style("opacity", 1);
      return s;
    }, (u) => u, (x) => x.remove());
    g.each(function (d) {
      const dir = d.cx > W * 0.55 ? -1 : 1;
      const lx = d.cx + dir * 28, ly = d.cy - 18;
      const s = d3.select(this);
      s.select("circle").attr("cx", d.cx).attr("cy", d.cy);
      s.select("line").attr("x1", d.cx).attr("y1", d.cy).attr("x2", lx).attr("y2", ly);
      s.select("text").attr("x", lx + dir * 3).attr("y", ly).attr("dy", "0.32em")
        .attr("text-anchor", dir > 0 ? "start" : "end").text(d.txt);
    });
  }

  // Passos (data-* no HTML definem a transição de cada um)
  const passos = [...document.querySelectorAll("#cap3 .passo")].map((el) => ({
    de: el.dataset.de, para: el.dataset.para, foco: (el.dataset.foco || "").split(",").filter(Boolean),
    robusto: el.dataset.robusto === "1", continuo: el.dataset.de !== el.dataset.para,
  }));
  function aplicar(i, p) {
    const s = passos[i];
    estado.de = s.de; estado.para = s.para; estado.foco = s.foco; estado.robusto = s.robusto;
    estado.t = s.continuo ? (reduzMovimento ? 1 : clamp01((p - 0.1) / 0.75)) : 1;
    desenhar(!s.continuo);
  }
  scrolly("#cap3 .passo", {
    onPasso: (i) => aplicar(i, passos[i].continuo ? 0 : 1),
    onProgresso: (i, p) => passos[i].continuo && aplicar(i, p),
  });

  aoRedimensionar(layout).observe(fig.querySelector(".mapa-svg"));
  layout();
}

// Legenda em blocos iguais (um por tom), já que os passos da escala não são uniformes.
function legenda(el, cor) {
  const passos = PASSOS_COBERTURA, bw = 36, H = 10, W = bw * passos.length;
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W + 24} 40`).attr("width", W + 24).attr("height", 40)
    .attr("aria-hidden", "true");
  const g = svg.append("g").attr("transform", "translate(12,4)");
  g.selectAll("rect").data(passos).join("rect").attr("x", (_, i) => i * bw).attr("width", bw - 2).attr("height", H)
    .attr("rx", 2).attr("fill", (v) => cor(v));
  g.selectAll("text").data(passos).join("text").attr("class", "rot-leg")
    .attr("x", (_, i) => i * bw + (bw - 2) / 2).attr("y", H + 14).attr("text-anchor", "middle")
    .text((v) => (v === 1 ? "≥100%" : v === passos[0] ? "≤60%" : `${Math.round(v * 100)}%`));
}
