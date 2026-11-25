// Capítulo 2 — Os suspeitos de sempre. Dispersão fixa (Y = esquema completo, pessoas ÷ Censo);
// a cada passo o eixo X muda de hipótese, com transição escalonada dos pontos. Cada hipótese
// termina com o carimbo "descartado". As hipóteses são variáveis, nunca municípios ou pessoas.
/* global d3 */
import { COR, DUR, EASE, fmt, reduzMovimento, scrolly, tooltip, aoRedimensionar } from "./util.js";

const FMT_X = {
  reais: (v) => `R$ ${fmt.int(v)}`,
  km: (v) => `${fmt.int(v)} km`,
  pct100: (v) => `${fmt.int(v)}%`,
  dec1: (v) => fmt.dec1(v),
  pct: (v) => fmt.pct(v),
};

export function initCap2(c2, municipios) {
  const fig = document.getElementById("g-dispersao");
  const nome = new Map(municipios.map((m) => [m.id, m.nome]));
  const dados = c2.municipios;
  const sus = new Map(c2.suspeitos.map((s) => [s.chave, s]));

  const svg = d3.select(fig.querySelector(".disp-svg")).append("svg").attr("role", "img")
    .attr("aria-labelledby", "g-disp-titulo g-disp-desc");
  svg.append("title").attr("id", "g-disp-titulo").text("Cobertura do esquema completo contra cada hipótese");
  const desc = svg.append("desc").attr("id", "g-disp-desc");
  const gGrade = svg.append("g").attr("class", "grade");
  const gX = svg.append("g").attr("class", "eixo eixo-x");
  const gY = svg.append("g").attr("class", "eixo eixo-y");
  const rotX = svg.append("text").attr("class", "rot-eixo").attr("text-anchor", "middle");
  const rotY = svg.append("text").attr("class", "rot-eixo").attr("text-anchor", "start").text("Esquema completo ↑");
  const gPts = svg.append("g").attr("class", "pontos");
  const gDest = svg.append("g").attr("class", "destaque-disp");
  const carimbo = d3.select(fig).select(".carimbo");

  let W, H, x, y, chave = "intro";
  const m = { t: 28, r: 18, b: 52, l: 48 };

  // posição X do passo de abertura: a ordem da própria cobertura (do menor ao maior)
  const ordem = new Map([...dados].sort((a, b) => a.y - b.y).map((d, i) => [d.id, i]));
  const xValor = (d) => (chave === "intro" ? ordem.get(d.id) : d[chave]);

  function escalas() {
    const vals = dados.map(xValor);
    x = d3.scaleLinear().domain(d3.extent(vals)).nice().range([m.l, W - m.r]);
  }

  function layout() {
    W = fig.querySelector(".disp-svg").clientWidth;
    H = Math.max(300, Math.min(520, fig.querySelector(".disp-svg").clientHeight || 440));
    if (window.innerWidth <= 860) H = Math.max(260, Math.min(H, window.innerHeight * 0.42)); // texto rola por baixo
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    y = d3.scaleLinear().domain([d3.min(dados, (d) => d.y) - 0.02, Math.max(1.02, d3.max(dados, (d) => d.y))])
      .nice().range([H - m.b, m.t]);
    gGrade.selectAll("line").data(y.ticks(5)).join("line").attr("x1", m.l).attr("x2", W - m.r)
      .attr("y1", y).attr("y2", y).attr("class", (v) => (v === 1 ? "cem" : null));
    gY.attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(8))
      .call((g) => g.select(".domain").remove());
    rotY.attr("x", m.l - 40).attr("y", m.t - 14);
    rotX.attr("x", (m.l + W - m.r) / 2).attr("y", H - 10);
    desenhar(false);
  }

  function desenhar(animar = true) {
    escalas();
    const s = sus.get(chave);
    const tAx = animar && !reduzMovimento ? gX.transition().duration(DUR).ease(EASE) : gX;
    gX.attr("transform", `translate(0,${H - m.b})`);
    tAx.call(d3.axisBottom(x).ticks(W < 520 ? 4 : 6).tickSizeOuter(0)
      .tickFormat(chave === "intro" ? () => "" : FMT_X[s.fmt]))
      .call((g) => g.select(".domain").attr("stroke", COR.grade));
    rotX.text(chave === "intro" ? "Municípios, do menor para o maior esquema completo →" : s.eixo);

    const pts = gPts.selectAll("circle").data(dados, (d) => d.id).join((e) => e.append("circle")
      .attr("r", 4.5).attr("cx", (d) => x(xValor(d))).attr("cy", (d) => y(d.y))
      .attr("fill", COR.azul).attr("fill-opacity", 0.78)
      // alerta: acima de 100% ganha anel terracota (valor real no detalhe)
      .attr("stroke", (d) => (d.y > 1 ? COR.terracota : COR.fundo)).attr("stroke-width", (d) => (d.y > 1 ? 2 : 1.5))
      .on("pointermove", (ev, d) => tooltip.mostrar(tt(d), ev.clientX, ev.clientY))
      .on("pointerleave", () => tooltip.esconder()));
    // entrada escalonada: os pontos andam da esquerda para a direita do novo eixo
    const xs = dados.map(xValor);
    const rk = d3.scaleLinear().domain(d3.extent(xs)).range([0, 1]);
    (animar && !reduzMovimento
      ? pts.transition().duration(DUR).ease(EASE).delay((d) => rk(xValor(d)) * 350)
      : pts).attr("cx", (d) => x(xValor(d))).attr("cy", (d) => y(d.y));

    // destaque: Fortaleza no passo do interior
    const dest = chave === "interior" ? dados.filter((d) => d.id === "2304400") : [];
    const g = gDest.selectAll("g").data(dest, (d) => d.id).join((e) => {
      const gg = e.append("g");
      gg.append("circle").attr("r", 7).attr("fill", "none").attr("stroke", COR.tinta).attr("stroke-width", 1.6);
      gg.append("text").attr("class", "rot-destaque").attr("dy", "-0.9em");
      return gg;
    });
    g.attr("transform", (d) => `translate(${x(xValor(d))},${y(d.y)})`)
      .select("text").attr("text-anchor", "start").attr("dx", 6).text((d) => `Fortaleza: ${fmt.pct(d.y)}`);

    desc.text(chave === "intro"
      ? "Os 184 municípios ordenados pela cobertura do esquema completo."
      : `Esquema completo contra ${s.eixo}. Correlação de postos ${fmt.rho(s.stats.rho)}; ` +
        `com controles, ${fmt.rho(s.stats.rho_parcial)}.`);
  }

  function tt(d) {
    const s = sus.get(chave);
    return `<strong>${nome.get(d.id)}</strong>
      <div class="tt-linha">Esquema completo <b>${fmt.pct1(d.y)}</b>${d.y > 1 ? ' <span class="alerta-icone" aria-label="acima de 100%">▲</span>' : ""}</div>
      ${chave === "intro" ? "" : `<div class="tt-linha">${s.titulo} <b>${FMT_X[s.fmt](d[chave])}</b></div>`}`;
  }

  function carimbar(mostrar) {
    carimbo.classed("visivel", false);
    if (!mostrar) return;
    // força reinício da animação curta (escala + rotação)
    void carimbo.node().offsetWidth;
    carimbo.classed("visivel", true);
  }

  const passos = [...document.querySelectorAll("#cap2 .passo")].map((el) => ({
    chave: el.dataset.x, carimbo: el.dataset.carimbo === "1",
  }));
  // o carimbo vem depois do argumento: quando metade do texto do passo já passou
  let carimbado = -1;
  scrolly("#cap2 .passo", {
    onPasso: (i) => {
      const novo = passos[i].chave;
      const mudou = novo !== chave;
      chave = novo;
      if (mudou) desenhar(true);
      carimbado = -1;
      carimbar(false);
      if (reduzMovimento && passos[i].carimbo) { carimbado = i; carimbar(true); }
    },
    onProgresso: (i, p) => {
      const deve = passos[i].carimbo && p > 0.4;
      if (deve && carimbado !== i) { carimbado = i; carimbar(true); }
      if (!deve && carimbado === i) { carimbado = -1; carimbar(false); }
    },
  });

  aoRedimensionar(layout).observe(fig.querySelector(".disp-svg"));
  layout();
}
