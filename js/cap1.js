// Capítulo 1 — O caso. Linha da cobertura acumulada (pessoas ÷ Censo 2022) que se desenha
// com a rolagem; faixa P10–P90 entre municípios que abre e congela; calendário de doses diárias.
/* global d3 */
import { COR, DUR, EASE, fmt, parseData, reduzMovimento, scrolly, tooltip, clamp01, lerp, MESES_CURTOS, aoRedimensionar } from "./util.js";

export function initCap1(dados) {
  linha(dados);
  calendario(dados);
}

// ======================================================================
// Linha + faixa
// ======================================================================
function linha(c) {
  const fig = document.getElementById("g-linha");
  const semanas = c.semanas.map(parseData);
  const n = semanas.length;
  const serie = semanas.map((d, i) => ({
    d, d1: c.estado_d1[i], comp: c.estado_comp[i], p10: c.p10[i], p90: c.p90[i],
  }));
  const D = (s) => parseData(s);
  const JUN21 = D("2021-06-30"), DEZ21 = D("2021-12-31"), FIM = semanas[n - 1];

  const svg = d3.select(fig).append("svg").attr("role", "img")
    .attr("aria-labelledby", "g-linha-titulo g-linha-desc");
  svg.append("title").attr("id", "g-linha-titulo").text("Cobertura acumulada no Ceará, 2021–2024");
  svg.append("desc").attr("id", "g-linha-desc").text(
    `Linhas da 1ª dose e do esquema completo, em pessoas ÷ população do Censo 2022, e faixa entre o 10º e o 90º ` +
    `percentil dos municípios no esquema completo. Ao fim: 1ª dose ${fmt.pct(c.marcos.estado_d1_fim)}, ` +
    `esquema completo ${fmt.pct(c.marcos.estado_comp_fim)}. Largura da faixa: ${fmt.pp(c.marcos.largura_jun21)} pontos ` +
    `em junho de 2021, ${fmt.pp(c.marcos.largura_dez21)} em dezembro de 2021 e ${fmt.pp(c.marcos.largura_fim)} no fim.`);

  const defs = svg.append("defs");
  const clipId = "clip-linha";
  const clipRect = defs.append("clipPath").attr("id", clipId).append("rect");
  const gGrade = svg.append("g").attr("class", "grade");
  const gEixoX = svg.append("g").attr("class", "eixo eixo-x");
  const gEixoY = svg.append("g").attr("class", "eixo eixo-y");
  const gDados = svg.append("g").attr("clip-path", `url(#${clipId})`);
  const faixa = gDados.append("path").attr("class", "faixa").attr("fill", COR.azul).attr("fill-opacity", 0);
  const lD1 = gDados.append("path").attr("class", "linha").attr("stroke", COR.terracota);
  const lComp = gDados.append("path").attr("class", "linha").attr("stroke", COR.azul);
  const gAnot = svg.append("g").attr("class", "anotacoes");
  const gCabeca = svg.append("g").attr("class", "cabecas");
  const hover = svg.append("g").attr("class", "hover").style("display", "none");
  hover.append("line").attr("class", "cruz");
  const alvo = svg.append("rect").attr("class", "alvo").attr("fill", "transparent");

  // legenda (2 séries → legenda sempre presente; rótulos diretos na ponta complementam)
  const leg = d3.select(fig).insert("div", "svg").attr("class", "legenda");
  [["1ª dose", COR.terracota, "linha"], ["Esquema completo", COR.azul, "linha"],
   ["Faixa entre municípios (10º–90º percentil, esquema completo)", COR.azul, "faixa"]]
    .forEach(([t, cor, tipo]) => {
      const it = leg.append("span").attr("class", "leg-item");
      it.append("span").attr("class", `leg-chave ${tipo}`).style("background", cor);
      it.append("span").text(t);
    });

  let W, H, x, y;
  const m = { t: 16, r: 92, b: 34, l: 44 };
  const estado = { revela: 0, faixa: 0, anot: 0 };

  function layout() {
    W = fig.clientWidth;
    const titulo = fig.querySelector(".grafico-titulo").offsetHeight + fig.querySelector(".legenda").offsetHeight;
    H = Math.max(260, Math.min(560, (fig.clientHeight || 500) - titulo - 24));
    // celular: o texto rola por cima da metade de baixo; o gráfico fica na de cima
    if (window.innerWidth <= 860) H = Math.max(240, Math.min(H, window.innerHeight * 0.5 - titulo));
    m.r = W < 520 ? 70 : 92;
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    x = d3.scaleUtc().domain([semanas[0], FIM]).range([m.l, W - m.r]);
    y = d3.scaleLinear().domain([0, Math.max(1, d3.max(c.p90))]).nice().range([H - m.b, m.t]);
    gGrade.selectAll("line").data(y.ticks(4)).join("line")
      .attr("x1", m.l).attr("x2", W - m.r).attr("y1", y).attr("y2", y)
      .attr("class", (v) => (v === 1 ? "cem" : null));
    gEixoY.attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(4).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(8))
      .call((g) => g.select(".domain").remove());
    gEixoX.attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(W < 520 ? d3.utcYear.every(1) : d3.utcMonth.every(6))
        .tickFormat((d) => (d.getUTCMonth() === 0 ? String(d.getUTCFullYear()) : MESES_CURTOS[d.getUTCMonth()]))
        .tickSizeOuter(0).tickSize(4))
      .call((g) => g.select(".domain").attr("stroke", COR.grade));
    faixa.attr("d", d3.area().x((d) => x(d.d)).y0((d) => y(d.p10)).y1((d) => y(d.p90)).curve(d3.curveMonotoneX)(serie));
    lD1.attr("d", d3.line().x((d) => x(d.d)).y((d) => y(d.d1)).curve(d3.curveMonotoneX)(serie));
    lComp.attr("d", d3.line().x((d) => x(d.d)).y((d) => y(d.comp)).curve(d3.curveMonotoneX)(serie));
    clipRect.attr("y", 0).attr("height", H);
    alvo.attr("x", m.l).attr("y", m.t).attr("width", W - m.l - m.r).attr("height", H - m.t - m.b);
    hover.select(".cruz").attr("y1", m.t).attr("y2", H - m.b);
    desenhar(false);
  }

  // revela ∈ [0,1] ao longo do eixo do tempo
  function dataRevelada() { return new Date(+semanas[0] + estado.revela * (+FIM - +semanas[0])); }

  function desenhar(animar = true) {
    const ate = dataRevelada();
    const xr = x(ate);
    clipRect.attr("x", m.l - 2).attr("width", Math.max(0, xr - m.l + 4));
    faixa.attr("fill-opacity", 0.16 * estado.faixa);
    // cabeças das linhas com o valor corrente (rótulo seletivo: só a ponta)
    const i = Math.max(0, d3.bisectRight(semanas, ate) - 1);
    const p = serie[i];
    const cab = [
      { k: "d1", v: p.d1, cor: COR.terracota, rot: "1ª dose" },
      { k: "comp", v: p.comp, cor: COR.azul, rot: "Completo" },
    ];
    const ys = cab.map((d) => y(d.v));
    if (Math.abs(ys[0] - ys[1]) < 30) { const mid = (ys[0] + ys[1]) / 2; ys[0] = mid - 15; ys[1] = mid + 15; }
    gCabeca.selectAll("g.cab").data(cab, (d) => d.k).join((e) => {
      const g = e.append("g").attr("class", "cab");
      g.append("circle").attr("r", 4.5);
      g.append("text").attr("class", "rot-valor").attr("x", 9).attr("dy", "0.32em");
      g.append("text").attr("class", "rot-serie").attr("x", 9).attr("dy", "1.5em");
      return g;
    })
      .style("opacity", estado.revela > 0.005 ? 1 : 0)
      .each(function (d, j) {
        const g = d3.select(this);
        g.select("circle").attr("cx", xr).attr("cy", y(d.v)).attr("fill", d.cor);
        g.selectAll("text").attr("transform", `translate(${xr},${ys[j]})`);
        g.select(".rot-valor").text(fmt.pct(d.v));
        g.select(".rot-serie").text(d.rot);
      });
    anotar(animar);
  }

  // anotações: largura da faixa em jun/21, dez/21 e no fim
  function anotar(animar) {
    const marcos = [
      { d: JUN21, larg: c.marcos.largura_jun21, rot: "jun/21" },
      { d: DEZ21, larg: c.marcos.largura_dez21, rot: "dez/21" },
      { d: FIM, larg: c.marcos.largura_fim, rot: "fim" },
    ].filter((k) => estado.anot > 0 && k.d <= dataRevelada());
    const at = (d) => serie[Math.max(0, d3.bisectRight(semanas, d) - 1)];
    const sel = gAnot.selectAll("g.marco").data(marcos, (k) => k.rot).join((e) => {
      const g = e.append("g").attr("class", "marco").style("opacity", 0);
      g.append("line").attr("class", "chave");
      g.append("line").attr("class", "ponta-a");
      g.append("line").attr("class", "ponta-b");
      g.append("text").attr("class", "rot-marco");
      return g;
    }, (u) => u, (s) => s.transition().duration(DUR / 2).style("opacity", 0).remove());
    sel.each(function (k, j) {
      const p = at(k.d);
      const xx = Math.min(x(k.d), W - m.r - 4);
      const ultimo = k.rot === "fim";
      const g = d3.select(this);
      g.select(".chave").attr("x1", xx).attr("x2", xx).attr("y1", y(p.p90)).attr("y2", y(p.p10));
      g.select(".ponta-a").attr("x1", xx - 4).attr("x2", xx + 4).attr("y1", y(p.p90)).attr("y2", y(p.p90));
      g.select(".ponta-b").attr("x1", xx - 4).attr("x2", xx + 4).attr("y1", y(p.p10)).attr("y2", y(p.p10));
      // rótulo abaixo e à direita da chave (área vazia sob a faixa); o último, à esquerda
      g.select(".rot-marco").attr("x", ultimo ? xx - 6 : xx + 6).attr("y", y(p.p10) + 15)
        .attr("text-anchor", ultimo ? "end" : "start")
        .text(`${fmt.pp(k.larg)} pontos`);
    });
    const alvoOp = estado.anot;
    (animar && !reduzMovimento ? sel.transition().duration(DUR).ease(EASE) : sel).style("opacity", alvoOp);
  }

  // hover: cruz + tooltip, só na parte já revelada
  alvo.on("pointermove", (ev) => {
    const [mx] = d3.pointer(ev);
    const d = x.invert(mx);
    if (d > dataRevelada()) { hover.style("display", "none"); tooltip.esconder(); return; }
    const p = serie[Math.max(0, d3.bisectRight(semanas, d) - 1)];
    hover.style("display", null).select(".cruz").attr("x1", x(p.d)).attr("x2", x(p.d));
    tooltip.mostrar(`<strong>Semana de ${fmt.dataCurta(p.d)}</strong>
      <div class="tt-linha"><span class="tt-chave" style="background:${COR.terracota}"></span>1ª dose <b>${fmt.pct1(p.d1)}</b></div>
      <div class="tt-linha"><span class="tt-chave" style="background:${COR.azul}"></span>Esquema completo <b>${fmt.pct1(p.comp)}</b></div>
      ${estado.faixa > 0.5 ? `<div class="tt-nota">80% dos municípios entre ${fmt.pct(p.p10)} e ${fmt.pct(p.p90)}</div>` : ""}`,
    ev.clientX, ev.clientY);
  }).on("pointerleave", () => { hover.style("display", "none"); tooltip.esconder(); });

  // Passos: 0 → desenha até jun/21; 1 → faixa aparece e linha vai até dez/21; 2 → até o fim
  // (a faixa congela); 3 → anotações da largura e correlação.
  const fr = (d) => (+d - +semanas[0]) / (+FIM - +semanas[0]);
  const ALVOS = [
    { de: 0, ate: fr(JUN21), faixa: [0, 0], anot: 0 },
    { de: fr(JUN21), ate: fr(DEZ21), faixa: [0, 1], anot: 0 },
    { de: fr(DEZ21), ate: 1, faixa: [1, 1], anot: 0 },
    { de: 1, ate: 1, faixa: [1, 1], anot: 1 },
  ];
  function aplicar(i, p) {
    const a = ALVOS[i];
    if (reduzMovimento) p = 1; // estados finais, sem interpolação
    estado.revela = lerp(a.de, a.ate, clamp01(p));
    estado.faixa = lerp(a.faixa[0], a.faixa[1], clamp01(p));
    estado.anot = a.anot;
    desenhar(true);
  }
  scrolly("#cap1 .passo", {
    onPasso: (i) => aplicar(i, reduzMovimento ? 1 : 0),
    onProgresso: (i, p) => aplicar(i, p),
  });

  aoRedimensionar(layout).observe(fig);
  layout();
}

// ======================================================================
// Calendário de doses diárias (dia × semana), um bloco por ano
// ======================================================================
function calendario(c) {
  const fig = document.getElementById("g-calendario");
  const dias = c.calendario.map(([s, v]) => ({ d: parseData(s), s, v }));
  const porAno = d3.groups(dias, (d) => d.d.getUTCFullYear());
  const limiares = [1000, 5000, 15000, 40000, 80000];
  const cor = d3.scaleThreshold().domain(limiares).range(COR.doses);
  const picos = new Set(c.picos.map((p) => p.data));

  // legenda de faixas
  const leg = d3.select(fig).insert("div", ":first-child").attr("class", "legenda legenda-faixas");
  leg.append("span").attr("class", "leg-titulo").text("Doses por dia");
  const rot = ["< 1 mil", "1–5 mil", "5–15 mil", "15–40 mil", "40–80 mil", "≥ 80 mil"];
  COR.doses.forEach((k, i) => {
    const it = leg.append("span").attr("class", "leg-item");
    it.append("span").attr("class", "leg-chave bloco").style("background", k);
    it.append("span").text(rot[i]);
  });

  const svg = d3.select(fig).append("svg").attr("role", "img").attr("aria-labelledby", "g-cal-titulo g-cal-desc");
  svg.append("title").attr("id", "g-cal-titulo").text("Doses aplicadas por dia a residentes do Ceará");
  svg.append("desc").attr("id", "g-cal-desc").text(
    `Calendário de ${fmt.dataCurta(c.periodo[0])} a ${fmt.dataCurta(c.periodo[1])}. Dia com mais doses: ` +
    `${fmt.data(c.picos[0].data)}, ${fmt.int(c.picos[0].doses)} doses.`);
  const g = svg.append("g");

  function layout() {
    const W = fig.clientWidth;
    const esq = 34;
    const cel = Math.max(4, Math.min(15, Math.floor((W - esq - 30) / 54)));
    const altAno = cel * 7 + 26;
    svg.attr("viewBox", `0 0 ${W} ${altAno * porAno.length + 8}`).attr("width", W)
      .attr("height", altAno * porAno.length + 8);
    const anos = g.selectAll("g.ano").data(porAno, (d) => d[0]).join((e) => {
      const a = e.append("g").attr("class", "ano");
      a.append("text").attr("class", "rot-ano");
      a.append("g").attr("class", "meses");
      a.append("g").attr("class", "celulas");
      return a;
    }).attr("transform", (_, i) => `translate(${esq},${i * altAno + 18})`);
    anos.select(".rot-ano").attr("x", -6).attr("y", cel * 3.5).attr("dy", "0.32em")
      .attr("text-anchor", "end").text((d) => d[0]);
    anos.each(function ([ano, ds]) {
      const inicio = d3.utcSunday.floor(new Date(Date.UTC(ano, 0, 1)));
      const col = (d) => d3.utcSunday.count(inicio, d);
      const a = d3.select(this);
      const ultimo = ds[ds.length - 1].d;
      a.selectAll("text.rot-sem").data([[1, "seg"], [3, "qua"], [5, "sex"]]).join("text").attr("class", "rot-sem")
        .attr("x", (cel * 54) + 4).attr("y", ([r]) => r * cel + cel / 2).attr("dy", "0.32em")
        .text(([, t]) => (cel >= 9 ? t : ""));
      a.select(".meses").selectAll("text").data(d3.utcMonths(new Date(Date.UTC(ano, 0, 1)), d3.utcDay.offset(ultimo, 1)))
        .join("text").attr("class", "rot-mes").attr("x", (d) => col(d3.utcSunday.ceil(d)) * cel).attr("y", -5)
        .text((d) => (cel >= 8 || d.getUTCMonth() % 3 === 0 ? MESES_CURTOS[d.getUTCMonth()] : ""));
      a.select(".celulas").selectAll("rect").data(ds, (d) => d.s).join("rect")
        .attr("x", (d) => col(d.d) * cel).attr("y", (d) => d.d.getUTCDay() * cel)
        .attr("width", cel - 1).attr("height", cel - 1).attr("rx", cel > 8 ? 2 : 1)
        .attr("fill", (d) => cor(d.v))
        .attr("class", (d) => (picos.has(d.s) ? "pico" : null));
    });
  }

  // tooltip: delegação no SVG inteiro (1.186 células)
  svg.on("pointermove", (ev) => {
    const d = d3.select(ev.target).datum();
    if (!d || !d.s) { tooltip.esconder(); return; }
    tooltip.mostrar(`<strong>${fmt.data(d.s)}</strong><div class="tt-linha">${fmt.int(d.v)} doses</div>
      ${picos.has(d.s) ? '<div class="tt-nota">Entre os 5 dias com mais doses</div>' : ""}`, ev.clientX, ev.clientY);
  }).on("pointerleave", () => tooltip.esconder());

  aoRedimensionar(layout).observe(fig);
  layout();
}
