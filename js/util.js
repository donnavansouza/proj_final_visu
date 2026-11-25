// Utilitários compartilhados: formatação pt-BR, preenchimento de cifras, cores, tooltip,
// movimento reduzido e scrollytelling. D3 e Scrollama chegam como globais (CDN).
/* global d3, scrollama */

export const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
export const DUR = reduzMovimento ? 0 : 750;
export const EASE = d3.easeCubicInOut;

// ---------- formatação ----------
const locale = d3.formatLocale({
  decimal: ",", thousands: ".", grouping: [3], currency: ["R$ ", ""], percent: " %",
});
const fmtInt = locale.format(",d");
const fmtDec = (n) => locale.format(`,.${n}f`);
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
  "setembro", "outubro", "novembro", "dezembro"];
const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
export const parseData = d3.utcParse("%Y-%m-%d");

export const fmt = {
  int: (v) => fmtInt(Math.round(v)),
  pct: (v) => `${fmtDec(0)(v * 100)}%`,
  pct1: (v) => `${fmtDec(1)(v * 100)}%`,
  pct2: (v) => `${fmtDec(2)(v * 100)}%`,
  pp: (v) => fmtDec(0)(v * 100),
  dec1: (v) => fmtDec(1)(v),
  dec2: (v) => fmtDec(2)(v),
  // correlação com sinal explícito: "+0,13", "−0,24"
  rho: (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${fmtDec(2)(Math.abs(v))}`,
  reais: (v) => `R$ ${fmtInt(Math.round(v))}`,
  p: (v) => (v < 0.001 ? "< 0,001" : fmtDec(3)(v)),
  dec3: (v) => fmtDec(3)(v),
  ordinal: (v) => `${fmtInt(v)}º`,
  milhoes: (v) => `${fmtDec(1)(v / 1e6)} milhões`,
  mil: (v) => `${fmtInt(Math.round(v / 1000))} mil`,
  data: (s) => { const d = typeof s === "string" ? parseData(s) : s; return `${d.getUTCDate()} de ${MESES[d.getUTCMonth()]} de ${d.getUTCFullYear()}`; },
  dataCurta: (s) => { const d = typeof s === "string" ? parseData(s) : s; return `${d.getUTCDate()} ${MESES_CURTOS[d.getUTCMonth()]} ${d.getUTCFullYear()}`; },
  mesAno: (d) => `${MESES_CURTOS[d.getUTCMonth()]} ${String(d.getUTCFullYear()).slice(2)}`,
};
export { MESES_CURTOS };

// Preenche <span data-v="cap1.marcos.rho_dez21_fim" data-f="dec2"> com o valor dos JSONs.
// Uma cifra que não existe nos dados aparece como {{TODO}} — nunca estimada.
export function preencher(raiz, dados) {
  raiz.querySelectorAll("[data-v]").forEach((el) => {
    const v = el.dataset.v.split(".").reduce((o, k) => (o == null ? undefined : o[k]), dados);
    const f = fmt[el.dataset.f || "int"];
    if (v == null || !f) {
      el.textContent = `{{TODO: ${el.dataset.v}}}`;
      el.classList.add("todo");
      console.warn("cifra ausente:", el.dataset.v);
    } else {
      el.textContent = f(v);
    }
  });
}

// Número que conta até o valor final quando entra na tela.
export function contar(el, valor, formatar, dur = 1600) {
  if (reduzMovimento) { el.textContent = formatar(valor); return; }
  const obs = new IntersectionObserver((ents) => {
    if (!ents[0].isIntersecting) return;
    obs.disconnect();
    const t0 = performance.now();
    const passo = (t) => {
      const k = Math.min(1, (t - t0) / dur);
      el.textContent = formatar(valor * d3.easeCubicOut(k));
      if (k < 1) requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
  }, { threshold: 0.6 });
  obs.observe(el);
}

// ---------- cores (validadas com dataviz/validate_palette.js contra o fundo #F6F0E4) ----------
export const COR = {
  tinta: "#1E1B18", tinta2: "#5E564C", grade: "#DCCFB6", fundo: "#F6F0E4",
  terracota: "#B5532E", azul: "#1E72A3",
  // cobertura: um só matiz (azul), claro → escuro; ponta clara 2,07:1 sobre o fundo
  cobertura: ["#86AFC4", "#6A9BB6", "#5086A6", "#3A7094", "#295B7E", "#1B4766", "#11344E"],
  // doses diárias: um só matiz (terracota); ponta clara 2,15:1 sobre o fundo
  doses: ["#D69873", "#CA7D52", "#BB653A", "#A44F28", "#863C1C", "#642A12"],
};

// Escala contínua da cobertura. O TETO EM 100% vale só para a cor; o valor real segue nos rótulos.
// Os tons ficam mais próximos no topo, onde está a maioria dos municípios (85–100%).
export const PASSOS_COBERTURA = [0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1];
export function escalaCobertura() {
  const s = d3.scaleLinear().domain(PASSOS_COBERTURA).range(COR.cobertura).interpolate(d3.interpolateLab).clamp(true);
  s.min = PASSOS_COBERTURA[0]; s.max = 1;
  return s;
}

// ---------- tooltip acessível (compartilhado) ----------
const tip = document.getElementById("tooltip");
export const tooltip = {
  mostrar(html, x, y) {
    tip.innerHTML = html;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    const px = Math.min(window.innerWidth - r.width - 12, Math.max(12, x + 14));
    const py = y - r.height - 14 < 8 ? y + 18 : y - r.height - 14;
    tip.style.transform = `translate(${px}px, ${py}px)`;
  },
  noElemento(html, el) {
    const r = el.getBoundingClientRect();
    this.mostrar(html, r.left + r.width / 2, r.top);
  },
  esconder() { tip.hidden = true; },
};

// ---------- scrollytelling ----------
// Scrollama com progresso contínuo. onPasso(i, dir) em cada degrau; onProgresso(i, p) contínuo.
// Sem sequestro de rolagem: a página rola normalmente.
export function scrolly(seletorPassos, { onPasso, onProgresso, offset = 0.6 }) {
  const s = scrollama();
  s.setup({ step: seletorPassos, offset, progress: !!onProgresso })
    .onStepEnter(({ index, element, direction }) => {
      document.querySelectorAll(seletorPassos).forEach((el) => el.classList.toggle("ativo", el === element));
      onPasso && onPasso(index, direction);
    });
  if (onProgresso) {
    // vários eventos por quadro viram um só redesenho (requestAnimationFrame)
    let pendente = null, quadro = 0;
    s.onStepProgress(({ index, progress }) => {
      pendente = [index, progress];
      if (!quadro) quadro = requestAnimationFrame(() => { quadro = 0; onProgresso(...pendente); });
    });
  }
  window.addEventListener("resize", () => s.resize());
  return s;
}

// Redesenha no redimensionamento, com espera curta.
export function aoRedimensionar(fn) {
  let t;
  const ro = new ResizeObserver(() => { clearTimeout(t); t = setTimeout(fn, 120); });
  return ro;
}

export const clamp01 = (x) => Math.max(0, Math.min(1, x));
export const lerp = (a, b, t) => a + (b - a) * t;
