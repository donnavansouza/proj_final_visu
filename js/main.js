// Ponto de entrada: carrega os JSONs gerados por scripts/preparar_site.py, preenche as cifras
// do texto e inicia cada capítulo.
/* global d3 */
import { preencher, contar, fmt } from "./util.js";
import { initCap1 } from "./cap1.js";
import { initCap2 } from "./cap2.js";
import { initCap3 } from "./cap3.js";
import { initCap4 } from "./cap4.js";
import { initCap5 } from "./cap5.js";
import { initCap7 } from "./cap7.js";

const carregar = (n) => d3.json(`json/${n}.json`);

try {
  const nomes = ["geo", "municipios", "cap1", "cap2", "cap3", "cap4", "cap5", "cap7"];
  const [geo, municipios, cap1, cap2, cap3, cap4, cap5, cap7] = await Promise.all(nomes.map(carregar));
  const s = Object.fromEntries(cap2.suspeitos.map((x) => [x.chave, x]));
  const dados = { cap1, cap2: { ...cap2, s }, cap3, cap4, cap5 };
  preencher(document, dados);

  contar(document.querySelector(".hero-num"), cap1.doses_total, fmt.milhoes);

  initCap1(cap1);
  initCap2(cap2, municipios);
  initCap3(geo, cap3, municipios);
  // capítulos mais pesados: inicializados quando estão a ~1,5 tela de distância
  // Preferência: quando o navegador estiver ocioso (enquanto o leitor está na abertura), um capítulo
  // por vez. Segurança: se o leitor chegar antes, inicializa ao se aproximar.
  const ocioso = window.requestIdleCallback || ((f) => setTimeout(f, 200));
  const aoChegar = (id, fn) => {
    let feito = false;
    const rodar = () => { if (!feito) { feito = true; obs.disconnect(); fn(); } };
    const obs = new IntersectionObserver((ents) => { if (ents.some((e) => e.isIntersecting)) rodar(); },
      { rootMargin: "150% 0px 150% 0px" });
    obs.observe(document.getElementById(id));
    return rodar;
  };
  const fila = [
    aoChegar("cap4", () => initCap4(cap4, cap2, geo, municipios)),
    aoChegar("cap5", () => initCap5(cap5, municipios)),
    aoChegar("cap7", () => initCap7(cap7, geo)),
  ];
  const proximo = () => { const f = fila.shift(); if (f) { f(); ocioso(proximo, { timeout: 3000 }); } };
  ocioso(proximo, { timeout: 3000 });
  document.body.classList.add("pronto");
} catch (e) {
  console.error(e);
  document.getElementById("erro-carga").hidden = false;
}
