// Capítulo 5 — O que fica em aberto. Reforço: o desfecho mais desigual (doses por habitante,
// nunca % de pessoas) e o único com sinal político. Duas figuras estáticas com tooltip.
/* global d3 */
import { COR, fmt, reduzMovimento, tooltip, aoRedimensionar } from "./util.js";

export function initCap5(c5, municipios) {
  const nome = new Map(municipios.map((m) => [m.id, m.nome]));
  enxame(c5, nome);
  dispersao(c5, nome);
}

function entrar(sel, el) {
  if (reduzMovimento) return;
  sel.attr("opacity", 0);
  const obs = new IntersectionObserver((ents) => {
    if (!ents[0].isIntersecting) return;
    obs.disconnect();
    sel.transition().duration(600).delay((_, i) => i * 3).attr("opacity", 1);
  }, { threshold: 0.3 });
  obs.observe(el);
}

// enxame (beeswarm) de reforço por habitante, com o 10º e o 90º percentil
function enxame(c5, nome) {
  const fig = document.getElementById("g-reforco");
  const svg = d3.select(fig).append("svg").attr("role", "img").attr("aria-labelledby", "g-ref-tit g-ref-desc");
  svg.append("title").attr("id", "g-ref-tit").text("Reforços por habitante nos 184 municípios");
  svg.append("desc").attr("id", "g-ref-desc").text(
    `Doses de reforço por habitante. 10º percentil: ${fmt.dec2(c5.p10)}; 90º percentil: ${fmt.dec2(c5.p90)}; ` +
    `o décimo superior aplicou ${fmt.dec2(c5.razao_p90_p10)} vezes as doses por habitante do inferior.`);
  const gX = svg.append("g").attr("class", "eixo eixo-x");
  const gRef = svg.append("g");
  const gPts = svg.append("g");
  let primeira = true;

  function layout() {
    const W = fig.clientWidth, H = W < 520 ? 230 : 210;
    const m = { t: 34, r: 16, b: 34, l: 16 };
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    const x = d3.scaleLinear().domain(d3.extent(c5.municipios, (d) => d.ref)).nice().range([m.l, W - m.r]);
    gX.attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => fmt.dec1(v)).tickSizeOuter(0))
      .call((g) => g.select(".domain").attr("stroke", COR.grade));
    // posições do enxame, calculadas uma vez por layout (sem animação de simulação)
    const nos = c5.municipios.map((d) => ({ ...d, x: x(d.ref), y: (H - m.b + m.t) / 2 }));
    const sim = d3.forceSimulation(nos).force("x", d3.forceX((d) => x(d.ref)).strength(1))
      .force("y", d3.forceY((H - m.b + m.t) / 2).strength(0.06)).force("c", d3.forceCollide(4.4)).stop();
    for (let i = 0; i < 160; i++) sim.tick();
    const sel = gPts.selectAll("circle").data(nos, (d) => d.id).join("circle").attr("r", 3.8)
      .attr("cx", (d) => d.x).attr("cy", (d) => Math.max(m.t, Math.min(H - m.b - 4, d.y)))
      .attr("fill", (d) => (d.ref <= c5.p10 || d.ref >= c5.p90 ? COR.terracota : COR.azul))
      .attr("stroke", COR.fundo).attr("stroke-width", 1)
      .on("pointermove", (ev, d) => tooltip.mostrar(`<strong>${nome.get(d.id)}</strong>
        <div class="tt-linha">Reforços por habitante <b>${fmt.dec2(d.ref)}</b></div>`, ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder());
    gRef.selectAll("*").remove();
    [[c5.p10, `10% com menos: até ${fmt.dec2(c5.p10)}`, "end"], [c5.p90, `10% com mais: ${fmt.dec2(c5.p90)} ou mais`, "start"]]
      .forEach(([v, t, a]) => {
        gRef.append("line").attr("class", "ref-funil").attr("x1", x(v)).attr("x2", x(v)).attr("y1", m.t - 6).attr("y2", H - m.b);
        gRef.append("text").attr("class", "rot-ref").attr("x", x(v) + (a === "end" ? -6 : 6)).attr("y", m.t - 12)
          .attr("text-anchor", a).text(t);
      });
    if (primeira) { entrar(sel, fig); primeira = false; }
  }
  aoRedimensionar(layout).observe(fig);
  layout();
}

// variação do voto em Bolsonaro 2018 → 2022 × reforços por habitante
function dispersao(c5, nome) {
  const fig = document.getElementById("g-ref-voto");
  const svg = d3.select(fig).append("svg").attr("role", "img").attr("aria-labelledby", "g-rv-tit g-rv-desc");
  svg.append("title").attr("id", "g-rv-tit").text("Variação do voto em Bolsonaro e reforços por habitante");
  svg.append("desc").attr("id", "g-rv-desc").text(
    `Correlação de postos ${fmt.rho(c5.var_bolsonaro.rho)}; com controles, ${fmt.rho(c5.var_bolsonaro.rho_parcial)}.`);
  const gG = svg.append("g").attr("class", "grade");
  const gX = svg.append("g").attr("class", "eixo eixo-x");
  const gY = svg.append("g").attr("class", "eixo eixo-y");
  const rx = svg.append("text").attr("class", "rot-eixo").attr("text-anchor", "middle")
    .text("Variação do voto em Bolsonaro, 2018 → 2022 (pontos percentuais) →");
  const ry = svg.append("text").attr("class", "rot-eixo").text("Reforços por habitante ↑");
  const gPts = svg.append("g");
  let primeira = true;

  function layout() {
    const W = fig.clientWidth, H = Math.min(380, Math.max(280, W * 0.62));
    const m = { t: 30, r: 16, b: 46, l: 44 };
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    const x = d3.scaleLinear().domain(d3.extent(c5.municipios, (d) => d.var)).nice().range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain(d3.extent(c5.municipios, (d) => d.ref)).nice().range([H - m.b, m.t]);
    gG.selectAll("line").data(y.ticks(5)).join("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y).attr("y2", y);
    gX.attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => fmt.int(v)).tickSizeOuter(0))
      .call((g) => g.select(".domain").attr("stroke", COR.grade));
    gY.attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat((v) => fmt.dec1(v)).tickSize(0).tickPadding(8))
      .call((g) => g.select(".domain").remove());
    rx.attr("x", (m.l + W - m.r) / 2).attr("y", H - 8);
    rx.text(W < 520 ? "Variação do voto, 2018 → 2022 (p.p.) →" : "Variação do voto em Bolsonaro, 2018 → 2022 (pontos percentuais) →");
    ry.attr("x", m.l - 36).attr("y", m.t - 14);
    const sel = gPts.selectAll("circle").data(c5.municipios, (d) => d.id).join("circle").attr("r", 4.2)
      .attr("cx", (d) => x(d.var)).attr("cy", (d) => y(d.ref)).attr("fill", COR.azul).attr("fill-opacity", 0.75)
      .attr("stroke", COR.fundo).attr("stroke-width", 1.2)
      .on("pointermove", (ev, d) => tooltip.mostrar(`<strong>${nome.get(d.id)}</strong>
        <div class="tt-linha">Variação do voto <b>${d.var > 0 ? "+" : ""}${fmt.dec1(d.var)} p.p.</b></div>
        <div class="tt-linha">Reforços por habitante <b>${fmt.dec2(d.ref)}</b></div>`, ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder());
    if (primeira) { entrar(sel, fig); primeira = false; }
  }
  aoRedimensionar(layout).observe(fig);
  layout();
}
