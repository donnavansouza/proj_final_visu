// Capítulo 7 — Explore você mesmo. Visões coordenadas sobre um estado único:
//   sel     → município selecionado (mapa, dispersão, paralelas, detalhe, tabela)
//   filtros → faixas por eixo das coordenadas paralelas (filtram mapa, dispersão e tabela)
//   x       → variável do eixo horizontal da dispersão
// Teclado: mapa e dispersão recebem foco; ←/→ percorrem municípios, Esc limpa. Os filtros têm
// campos numéricos equivalentes ao pincel; a tabela é a versão completa e acessível dos dados.
/* global d3 */
import { COR, DUR, EASE, fmt, reduzMovimento, tooltip, escalaCobertura, aoRedimensionar } from "./util.js";
import { PERFIS } from "./cap4.js";

const EIXOS_PARALELAS = ["d1", "comp", "aband", "ref", "renda", "voto", "esf"];
const OPCOES_X = ["renda", "dist", "voto", "varvoto", "esf", "flu", "evang", "rural", "d1", "aband", "ref", "pop"];

export function initCap7(c7, geo) {
  const V = c7.variaveis;
  const muns = c7.municipios;
  const porId = new Map(muns.map((m) => [m.id, m]));
  const porNome = [...muns].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  const F = {
    pct: (v) => fmt.pct1(v), dec2: (v) => fmt.dec2(v), dec1: (v) => fmt.dec1(v), int: (v) => fmt.int(v),
    reais: (v) => `R$ ${fmt.int(v)}`, pct100: (v) => `${fmt.dec1(v)}%`, km: (v) => `${fmt.int(v)} km`,
  };
  const f = (k, v) => (v == null ? "—" : F[V[k].fmt](v));
  const cor = escalaCobertura();

  const estado = { sel: null, filtros: {}, x: "renda" };
  const ouvintes = [];
  const emitir = () => ouvintes.forEach((fn) => fn());
  const passa = (m) => Object.entries(estado.filtros).every(([k, [a, b]]) => m[k] >= a && m[k] <= b);
  const selecionar = (id, origem) => {
    estado.sel = id === estado.sel && origem === "clique" ? null : id;
    emitir();
  };
  const anunciar = (t) => { document.getElementById("exp-status").textContent = t; };

  // ======================= barra: busca, eixo X, limpar =======================
  // Tom Select (busca com acentos ignorados + combobox acessível) nos dois campos da barra.
  /* global TomSelect */
  const ponto = (m) => (m.perfil ? `<span class="op-ponto" style="background:${PERFIS[m.perfil].cor}" title="${PERFIS[m.perfil].rot}"></span>` : "");
  const busca = new TomSelect("#busca", {
    options: porNome.map((m) => ({ value: m.id, text: m.nome, comp: m.comp, perfil: m.perfil })),
    valueField: "value", labelField: "text", searchField: ["text"], maxItems: 1, maxOptions: 200,
    placeholder: "Digite o nome do município", allowEmptyOption: true, closeAfterSelect: true,
    render: {
      option: (d, esc) => `<div class="op-mun"><span>${ponto(porId.get(d.value))}${esc(d.text)}</span>
        <span class="op-valor">${f("comp", d.comp)}</span></div>`,
      item: (d, esc) => `<div>${esc(d.text)}</div>`,
      no_results: (d, esc) => `<div class="no-results">Nenhum município com "${esc(d.input)}"</div>`,
    },
    onChange: (id) => { if (id && id !== estado.sel) selecionar(id, "busca"); },
  });
  const sincronizarBusca = () => {
    const atual = busca.getValue();
    if ((estado.sel || "") !== atual) estado.sel ? busca.setValue(estado.sel, true) : busca.clear(true);
  };

  const GRUPOS = [["vac", "Vacinação", ["d1", "aband", "ref"]], ["soc", "Território e renda", ["renda", "dist", "rural", "pop"]],
    ["pol", "Política", ["voto", "varvoto"]], ["sau", "Saúde e hábito", ["esf", "flu"]], ["cul", "Religião", ["evang"]]];
  const grupoDe = Object.fromEntries(GRUPOS.flatMap(([g, , ks]) => ks.map((k) => [k, g])));
  console.assert(OPCOES_X.every((k) => grupoDe[k]), "variável sem grupo no seletor");
  // Seletor do eixo X: <select> nativo estilizado (12 opções, sem busca). Duas instâncias da
  // Tom Select juntas fazem o primeiro clique só desfocar a outra; o nativo é mais confiável.
  const selX = d3.select("#sel-x");
  selX.selectAll("optgroup").data(GRUPOS).join("optgroup").attr("label", (g) => g[1])
    .selectAll("option").data((g) => g[2]).join("option").attr("value", (k) => k).text((k) => V[k].rot);
  selX.property("value", estado.x).on("change", function () { estado.x = this.value; emitir(); });

  document.getElementById("limpar").addEventListener("click", () => {
    estado.filtros = {};
    paralelas.limparPinceis();
    campos.limpar();
    emitir();
  });

  // ======================= mapa =======================
  const mapa = (() => {
    const box = document.querySelector("#exp-mapa .exp-svg");
    const svg = d3.select(box).append("svg").attr("tabindex", 0).attr("role", "application")
      .attr("aria-label", "Mapa do esquema completo por município. Use as setas para percorrer os municípios em ordem alfabética e Esc para limpar a seleção.");
    const g = svg.append("g");
    const gSel = svg.append("g").attr("class", "exp-sel-mapa");
    let path;
    function layout() {
      const W = box.clientWidth, H = Math.min(W * 1.02, 520);
      svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
      path = d3.geoPath(d3.geoMercator().fitExtent([[6, 6], [W - 6, H - 6]], geo));
      g.selectAll("path").data(geo.features, (d) => d.id).join("path").attr("d", path)
        .on("click", (ev, d) => selecionar(d.id, "clique"))
        .on("pointermove", (ev, d) => tooltip.mostrar(tt(d.id), ev.clientX, ev.clientY))
        .on("pointerleave", () => tooltip.esconder());
      render();
    }
    function render() {
      g.selectAll("path")
        .attr("fill", (d) => cor(porId.get(d.id).comp))
        .classed("fora", (d) => !passa(porId.get(d.id)))
        .classed("acima", (d) => porId.get(d.id).comp > 1);
      const s = estado.sel ? geo.features.filter((d) => d.id === estado.sel) : [];
      gSel.selectAll("path").data(s, (d) => d.id).join("path").attr("d", path);
    }
    svg.on("keydown", (ev) => teclado(ev, porNome.filter(passa).map((m) => m.id), svg.node(), (id) => {
      const fe = geo.features.find((x) => x.id === id);
      const [cx, cy] = path.centroid(fe);
      const r = svg.node().getBoundingClientRect();
      tooltip.mostrar(tt(id), r.left + cx, r.top + cy);
    }));
    svg.on("blur", () => tooltip.esconder());
    aoRedimensionar(layout).observe(box);
    layout();
    return { layout, render };
  })();

  // ======================= dispersão =======================
  const disp = (() => {
    const box = document.querySelector("#exp-disp .exp-svg");
    const svg = d3.select(box).append("svg").attr("tabindex", 0).attr("role", "application");
    const gG = svg.append("g").attr("class", "grade");
    const gX = svg.append("g").attr("class", "eixo eixo-x");
    const gY = svg.append("g").attr("class", "eixo eixo-y");
    const rx = svg.append("text").attr("class", "rot-eixo").attr("text-anchor", "middle");
    const ry = svg.append("text").attr("class", "rot-eixo").text("Esquema completo ↑");
    const gP = svg.append("g");
    const gS = svg.append("g").attr("class", "exp-sel-ponto");
    let W, H, x, y;
    const m = { t: 26, r: 14, b: 46, l: 46 };
    function layout() {
      W = box.clientWidth; H = Math.min(Math.max(280, W * 0.85), 480);
      svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
      y = d3.scaleLinear().domain(d3.extent(muns, (d) => d.comp)).nice().range([H - m.b, m.t]);
      gG.selectAll("line").data(y.ticks(5)).join("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y).attr("y2", y)
        .attr("class", (v) => (v === 1 ? "cem" : null));
      gY.attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(8))
        .call((s) => s.select(".domain").remove());
      ry.attr("x", m.l - 38).attr("y", m.t - 12);
      rx.attr("x", (m.l + W - m.r) / 2).attr("y", H - 8);
      render(false);
    }
    let xAnterior = null;
    function render(animar = true) {
      const k = estado.x;
      x = d3.scaleLinear().domain(d3.extent(muns, (d) => d[k])).nice().range([m.l, W - m.r]);
      const mudouX = xAnterior !== k; xAnterior = k;
      const t = (s) => (animar && mudouX && !reduzMovimento ? s.transition().duration(DUR).ease(EASE) : s);
      t(gX.attr("transform", `translate(0,${H - m.b})`)).call(d3.axisBottom(x).ticks(W < 420 ? 4 : 6).tickFormat((v) => F[V[k].fmt](v)).tickSizeOuter(0))
        .call((s) => s.select(".domain").attr("stroke", COR.grade));
      rx.text(`${V[k].rot} →`);
      svg.attr("aria-label", `Dispersão: esquema completo contra ${V[k].rot}. Use as setas para percorrer os municípios da esquerda para a direita e Esc para limpar.`);
      const sel = gP.selectAll("circle").data(muns, (d) => d.id).join((e) => e.append("circle").attr("r", 4)
        .attr("cx", (d) => x(d[k])).attr("cy", (d) => y(d.comp))
        .on("click", (ev, d) => selecionar(d.id, "clique"))
        .on("pointermove", (ev, d) => tooltip.mostrar(tt(d.id), ev.clientX, ev.clientY))
        .on("pointerleave", () => tooltip.esconder()));
      sel.classed("fora", (d) => !passa(d)).classed("acima", (d) => d.comp > 1);
      t(sel).attr("cx", (d) => x(d[k])).attr("cy", (d) => y(d.comp));
      const s = estado.sel ? [porId.get(estado.sel)] : [];
      const gs = gS.selectAll("g").data(s, (d) => d.id).join((e) => {
        const gg = e.append("g");
        gg.append("circle").attr("r", 8);
        gg.append("text").attr("dy", "-0.9em");
        return gg;
      });
      t(gs).attr("transform", (d) => `translate(${x(d[k])},${y(d.comp)})`);
      gs.select("text").attr("text-anchor", (d) => (x(d[k]) > W * 0.7 ? "end" : "start")).text((d) => d.nome);
    }
    svg.on("keydown", (ev) => {
      const ordem = muns.filter(passa).sort((a, b) => a[estado.x] - b[estado.x]).map((m) => m.id);
      teclado(ev, ordem, svg.node(), (id) => {
        const d = porId.get(id);
        const r = svg.node().getBoundingClientRect();
        tooltip.mostrar(tt(id), r.left + x(d[estado.x]), r.top + y(d.comp));
      });
    });
    svg.on("blur", () => tooltip.esconder());
    aoRedimensionar(layout).observe(box);
    layout();
    return { layout, render };
  })();

  // navegação por teclado compartilhada (mapa e dispersão)
  function teclado(ev, ordem, alvo, mostrar) {
    if (!ordem.length) return;
    const i = ordem.indexOf(estado.sel);
    let j = null;
    if (ev.key === "ArrowRight" || ev.key === "ArrowDown") j = i < 0 ? 0 : (i + 1) % ordem.length;
    else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") j = i < 0 ? ordem.length - 1 : (i - 1 + ordem.length) % ordem.length;
    else if (ev.key === "Home") j = 0;
    else if (ev.key === "End") j = ordem.length - 1;
    else if (ev.key === "Escape") { estado.sel = null; emitir(); tooltip.esconder(); return; }
    if (j == null) return;
    ev.preventDefault();
    selecionar(ordem[j], "teclado");
    mostrar(ordem[j]);
  }

  function tt(id) {
    const m = porId.get(id);
    return `<strong>${m.nome}</strong>
      <div class="tt-linha">Esquema completo <b>${f("comp", m.comp)}</b>${m.comp > 1 ? ' <span class="alerta-icone" aria-label="acima de 100%">▲</span>' : ""}</div>
      <div class="tt-linha">${V[estado.x].rot.split(",")[0]} <b>${f(estado.x, m[estado.x])}</b></div>`;
  }

  // ======================= coordenadas paralelas =======================
  const paralelas = (() => {
    const box = document.querySelector("#exp-paralelas .exp-svg");
    const svg = d3.select(box).append("svg").attr("role", "img")
      .attr("aria-label", "Coordenadas paralelas: cada linha é um município, cruzando sete eixos. Arraste sobre um eixo para filtrar; os mesmos filtros estão disponíveis em campos numéricos logo abaixo.");
    const gL = svg.append("g").attr("class", "par-linhas");
    const gSel = svg.append("g").attr("class", "par-sel");
    const gE = svg.append("g").attr("class", "par-eixos");
    let W, H, xp, ys = {}, pinceis = {}, movendo = false;
    const m = { t: 40, r: 30, b: 16, l: 30 };
    function layout() {
      W = box.clientWidth; H = W < 600 ? 300 : 340;
      svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
      xp = d3.scalePoint().domain(EIXOS_PARALELAS).range([m.l + 30, W - m.r - 30]);
      EIXOS_PARALELAS.forEach((k) => { ys[k] = d3.scaleLinear().domain(d3.extent(muns, (d) => d[k])).nice().range([H - m.b, m.t]); });
      const linha = (d) => d3.line()(EIXOS_PARALELAS.map((k) => [xp(k), ys[k](d[k])]));
      gL.selectAll("path").data(muns, (d) => d.id).join("path").attr("d", linha)
        .on("click", (ev, d) => selecionar(d.id, "clique"))
        .on("pointermove", (ev, d) => tooltip.mostrar(tt(d.id), ev.clientX, ev.clientY))
        .on("pointerleave", () => tooltip.esconder());
      const eixos = gE.selectAll("g.par-eixo").data(EIXOS_PARALELAS).join((e) => {
        const g = e.append("g").attr("class", "par-eixo");
        g.append("g").attr("class", "eixo");
        g.append("text").attr("class", "par-titulo");
        g.append("g").attr("class", "pincel");
        return g;
      }).attr("transform", (k) => `translate(${xp(k)},0)`);
      eixos.select(".eixo").each(function (k) {
        d3.select(this).call(d3.axisLeft(ys[k]).ticks(5).tickFormat((v) => F[V[k].fmt](v).replace(",0%", "%")).tickSize(3));
      });
      const curto = { d1: "1ª dose", comp: "Completo", aband: "Abandono", ref: "Reforço/hab.", renda: "Renda", voto: "Voto 2018", esf: "Equipes/10 mil" };
      eixos.select(".par-titulo").attr("y", m.t - 16).attr("text-anchor", "middle").text((k) => curto[k]);
      eixos.select(".pincel").each(function (k) {
        const b = d3.brushY().extent([[-12, m.t], [12, H - m.b]])
          .on("brush end", (ev) => {
            if (movendo) return;
            if (!ev.selection) delete estado.filtros[k];
            else estado.filtros[k] = ev.selection.map(ys[k].invert).sort((a, b) => a - b);
            campos.sincronizar(k);
            emitir();
          });
        pinceis[k] = { b, g: d3.select(this) };
        d3.select(this).call(b);
        const f = estado.filtros[k];
        movendo = true;
        d3.select(this).call(b.move, f ? f.map(ys[k]).sort((a, c) => a - c) : null);
        movendo = false;
      });
      render();
    }
    function render() {
      gL.selectAll("path").classed("fora", (d) => !passa(d)).classed("perfil", (d) => !!d.perfil);
      const s = estado.sel ? [porId.get(estado.sel)] : [];
      gSel.selectAll("path").data(s, (d) => d.id).join("path")
        .attr("d", (d) => d3.line()(EIXOS_PARALELAS.map((k) => [xp(k), ys[k](d[k])])));
    }
    function mover(k, faixa) {   // chamado pelos campos numéricos
      const p = pinceis[k];
      movendo = true;
      p.g.call(p.b.move, faixa ? faixa.map(ys[k]).sort((a, b) => a - b) : null);
      movendo = false;
    }
    function limparPinceis() { EIXOS_PARALELAS.forEach((k) => mover(k, null)); }
    aoRedimensionar(layout).observe(box);
    layout();
    return { layout, render, mover, limparPinceis, ys: () => ys };
  })();

  // ======================= filtros por faixa: sliders de duas alças (noUiSlider) =======================
  // Equivalentes ao pincel das paralelas e sincronizados com ele nos dois sentidos. Cada alça é um
  // role="slider" acessível por teclado (setas, PageUp/PageDown, Home/End), com o valor anunciado.
  // Acima de cada slider, um mini-histograma: em claro, os 184 municípios; em azul, os que passam
  // em todos os filtros ativos.
  /* global noUiSlider */
  const campos = (() => {
    const CURTO = { d1: "1ª dose", comp: "Esquema completo", aband: "Abandono", ref: "Reforços por habitante",
      renda: "Renda per capita mediana", voto: "Voto em Bolsonaro, 2018", esf: "Equipes de Saúde da Família / 10 mil" };
    const PASSO = { pct: 0.005, dec2: 0.01, reais: 10, pct100: 0.5, dec1: 0.1 };
    const ext = Object.fromEntries(EIXOS_PARALELAS.map((k) => [k, d3.extent(muns, (d) => d[k])]));
    const bins = Object.fromEntries(EIXOS_PARALELAS.map((k) => [k, d3.bin().domain(ext[k]).thresholds(24)(muns.map((d) => d[k]))]));
    const raiz = d3.select("#exp-filtros-campos");
    const cartoes = raiz.selectAll("div.filtro").data(EIXOS_PARALELAS).join((e) => {
      const c = e.append("div").attr("class", "filtro");
      const cab = c.append("div").attr("class", "filtro-cab");
      cab.append("span").attr("class", "filtro-nome").attr("id", (k) => `filtro-nome-${k}`).text((k) => CURTO[k]);
      cab.append("span").attr("class", "filtro-faixa");
      c.append("svg").attr("class", "filtro-hist").attr("aria-hidden", "true").attr("preserveAspectRatio", "none")
        .attr("viewBox", "0 0 100 28");
      c.append("div").attr("class", "filtro-slider");
      return c;
    });
    const sliders = {};
    let externo = false;   // true enquanto o pincel atualiza o slider (evita laço)
    let quadro = null;

    cartoes.each(function (k) {
      const el = d3.select(this).select(".filtro-slider").node();
      const formato = { to: (v) => F[V[k].fmt](+v), from: Number };
      const s = noUiSlider.create(el, {
        start: ext[k], connect: true, range: { min: ext[k][0], max: ext[k][1] },
        step: PASSO[V[k].fmt], behaviour: "drag-tap", ariaFormat: formato,
        handleAttributes: [{ "aria-label": `${CURTO[k]}, valor mínimo` }, { "aria-label": `${CURTO[k]}, valor máximo` }],
      });
      sliders[k] = s;
      s.on("update", () => faixa(k));
      s.on("slide", () => {
        if (externo) return;
        const [a, b] = s.get(true);
        const cheio = a <= ext[k][0] + 1e-9 && b >= ext[k][1] - 1e-9;
        if (cheio) delete estado.filtros[k]; else estado.filtros[k] = [a, b];
        paralelas.mover(k, estado.filtros[k] || null);
        // um redesenho por quadro durante o arraste
        if (!quadro) quadro = requestAnimationFrame(() => { quadro = null; emitir(); });
      });
    });

    function faixa(k) {
      const [a, b] = sliders[k].get(true);
      const ativo = !!estado.filtros[k];
      raiz.selectAll("div.filtro").filter((d) => d === k).classed("ativo", ativo)
        .select(".filtro-faixa").text(`${F[V[k].fmt](a)} – ${F[V[k].fmt](b)}`);
    }

    function histogramas() {
      const passam = muns.filter(passa);
      cartoes.each(function (k) {
        const bs = bins[k];
        const n = d3.max(bs, (b) => b.length);
        const x = d3.scaleLinear().domain(ext[k]).range([0, 100]);
        const y = d3.scaleLinear().domain([0, n]).range([28, 1]);
        const cont = bs.map((b) => passam.filter((m) => m[k] >= b.x0 && (m[k] < b.x1 || b.x1 === ext[k][1])).length);
        const svg = d3.select(this).select("svg");
        const larg = (b) => Math.max(0.5, x(b.x1) - x(b.x0) - 0.6);
        svg.selectAll("rect.todos").data(bs).join("rect").attr("class", "todos")
          .attr("x", (b) => x(b.x0)).attr("width", larg).attr("y", (b) => y(b.length)).attr("height", (b) => 28 - y(b.length));
        svg.selectAll("rect.passam").data(bs).join("rect").attr("class", "passam")
          .attr("x", (b) => x(b.x0)).attr("width", larg).attr("y", (_, i) => y(cont[i])).attr("height", (_, i) => 28 - y(cont[i]));
      });
    }

    function sincronizar(k) {   // pincel → slider
      externo = true;
      sliders[k].set(estado.filtros[k] || ext[k]);
      externo = false;
      faixa(k);
    }
    return { sincronizar, histogramas, limpar: () => EIXOS_PARALELAS.forEach(sincronizar) };
  })();

  // ======================= detalhe =======================
  const detalhe = (() => {
    const el = d3.select("#exp-detalhe");
    const vazio = el.select(".det-vazio");
    const cheio = el.select(".det-cheio");
    const svg = cheio.select(".det-serie").append("svg").attr("role", "img");
    const meses = c7.meses.map((s) => d3.utcParse("%Y-%m")(s));
    function render() {
      const m = estado.sel ? porId.get(estado.sel) : null;
      vazio.style("display", m ? "none" : null);
      cheio.style("display", m ? null : "none");
      if (!m) return;
      cheio.select(".det-nome").text(m.nome);
      const tags = [];
      if (m.perfil) tags.push(`<span class="tag" style="--c:${PERFIS[m.perfil].cor}">${PERFIS[m.perfil].rot}</span>`);
      if (m.sensivel) tags.push('<span class="tag tag-neutra">Sensível ao denominador</span>');
      if (m.acima100_robusto) tags.push('<span class="tag tag-alerta">▲ 1ª dose acima de 100% com os dois denominadores</span>');
      if (m.rmf) tags.push('<span class="tag tag-neutra">Região Metropolitana</span>');
      cheio.select(".det-tags").html(tags.join(" "));
      const rank = 1 + muns.filter((x) => x.comp > m.comp).length;
      const linhas = [["d1"], ["comp", `${rank}º de 184`], ["aband"], ["ref"], ["renda"], ["voto"], ["esf"], ["pop"]];
      cheio.select(".det-numeros").html(linhas.map(([k, extra]) =>
        `<div><dt>${V[k].rot}</dt><dd>${f(k, m[k])}${(k === "d1" || k === "comp") && m[k] > 1 ? ' <span class="alerta-icone" aria-label="acima de 100%">▲</span>' : ""}${extra ? ` <small>${extra}</small>` : ""}</dd></div>`).join(""));
      serie(m);
      anunciar(`${m.nome} selecionado: esquema completo ${f("comp", m.comp)}, abandono ${f("aband", m.aband)}.`);
    }
    function serie(m) {
      const W = cheio.select(".det-serie").node().clientWidth || 300, H = 150;
      const mg = { t: 10, r: 62, b: 22, l: 34 };
      svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H)
        .attr("aria-label", `Cobertura acumulada de ${m.nome}: 1ª dose chega a ${f("d1", m.d1)} e esquema completo a ${f("comp", m.comp)}.`);
      const x = d3.scaleUtc().domain(d3.extent(meses)).range([mg.l, W - mg.r]);
      const yMax = Math.max(1, d3.max(m.s_d1) / 1000);
      const y = d3.scaleLinear().domain([0, yMax]).nice().range([H - mg.b, mg.t]);
      svg.selectAll("*").remove();
      svg.append("g").attr("class", "grade").selectAll("line").data(y.ticks(3)).join("line")
        .attr("x1", mg.l).attr("x2", W - mg.r).attr("y1", y).attr("y2", y).attr("class", (v) => (v === 1 ? "cem" : null));
      svg.append("g").attr("class", "eixo").attr("transform", `translate(${mg.l},0)`)
        .call(d3.axisLeft(y).ticks(3).tickFormat((v) => `${Math.round(v * 100)}%`).tickSize(0).tickPadding(6)).call((g) => g.select(".domain").remove());
      svg.append("g").attr("class", "eixo").attr("transform", `translate(0,${H - mg.b})`)
        .call(d3.axisBottom(x).ticks(d3.utcYear.every(1)).tickFormat(d3.utcFormat("%Y")).tickSizeOuter(0));
      const ln = (arr, div = 1000) => d3.line().x((_, i) => x(meses[i])).y((v) => y(v / div))(arr);
      svg.append("path").attr("class", "linha det-estado").attr("d", ln(c7.estado.comp, 1)).attr("stroke", "#A89C88").attr("stroke-width", 1.5);
      svg.append("path").attr("class", "linha").attr("d", ln(m.s_d1)).attr("stroke", COR.terracota);
      svg.append("path").attr("class", "linha").attr("d", ln(m.s_comp)).attr("stroke", COR.azul);
      [["1ª dose", m.s_d1, COR.terracota], ["Completo", m.s_comp, COR.azul]].forEach(([t, arr], i) => {
        const yy = y(arr[arr.length - 1] / 1000) + (i === 0 ? -6 : 8);
        svg.append("text").attr("class", "rot-serie").attr("x", W - mg.r + 4).attr("y", yy).attr("dy", "0.32em").text(t);
      });
    }
    return { render };
  })();

  // ======================= tabela (versão acessível e completa) =======================
  const tabela = (() => {
    const cols = ["nome", "d1", "comp", "aband", "ref", "renda", "voto", "esf"];
    const rot = { nome: "Município", d1: "1ª dose", comp: "Completo", aband: "Abandono", ref: "Reforço/hab.", renda: "Renda", voto: "Voto 2018", esf: "Equipes/10 mil" };
    let ordem = { k: "comp", asc: true };
    const tb = d3.select("#exp-tabela table");
    const th = tb.select("thead tr").selectAll("th").data(cols).join("th").attr("scope", "col");
    th.selectAll("button").data((k) => [k]).join("button").attr("type", "button").text((k) => rot[k])
      .on("click", (ev, k) => { ordem = { k, asc: ordem.k === k ? !ordem.asc : true }; render(); });
    function render() {
      th.attr("aria-sort", (k) => (k === ordem.k ? (ordem.asc ? "ascending" : "descending") : "none"));
      const linhas = muns.filter(passa).sort((a, b) => {
        const v = ordem.k === "nome" ? a.nome.localeCompare(b.nome, "pt-BR") : a[ordem.k] - b[ordem.k];
        return ordem.asc ? v : -v;
      });
      d3.select("#exp-tabela .tab-contagem").text(`${linhas.length} de 184 municípios${Object.keys(estado.filtros).length ? " (com filtros)" : ""}`);
      const tr = tb.select("tbody").selectAll("tr").data(linhas, (d) => d.id).join("tr").order()
        .classed("selecionado", (d) => d.id === estado.sel);
      tr.selectAll("td,th").data((d) => cols.map((k) => ({ k, d }))).join((e) => e.append((x) => document.createElement(x.k === "nome" ? "th" : "td")))
        .attr("scope", (x) => (x.k === "nome" ? "row" : null))
        .html((x) => (x.k === "nome"
          ? `<button type="button" class="link-sel">${x.d.nome}</button>`
          : `${f(x.k, x.d[x.k])}${(x.k === "d1" || x.k === "comp") && x.d[x.k] > 1 ? " ▲" : ""}`));
      tr.select("button.link-sel").on("click", (ev, d) => {
        selecionar(d.id, "tabela");
        document.getElementById("exp-detalhe").scrollIntoView({ behavior: reduzMovimento ? "auto" : "smooth", block: "nearest" });
      });
    }
    return { render };
  })();

  // ======================= ligação geral =======================
  ouvintes.push(() => {
    mapa.render(); disp.render(); paralelas.render(); detalhe.render(); tabela.render(); campos.histogramas();
    const n = muns.filter(passa).length;
    const comFiltro = Object.keys(estado.filtros).length > 0;
    d3.select("#exp-contagem").classed("ativo", comFiltro)
      .html(comFiltro ? `<b>${n}</b> de 184 municípios` : "Todos os 184 municípios");
    document.getElementById("limpar").disabled = !comFiltro;
    sincronizarBusca();
    if (!estado.sel && !Object.keys(estado.filtros).length) anunciar("");
  });
  emitir();
}
