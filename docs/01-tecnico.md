# 1. Como o site funciona (parte técnica)

> Objetivo deste documento: entender cada peça do site a ponto de conseguir explicá-la, alterá-la e
> recriá-la. Ao final há perguntas de revisão.

## 1.1 Visão geral

O site é **uma única página** (`index.html`) sem framework e sem etapa de *build*: o navegador baixa
HTML, CSS, os módulos JavaScript e os JSONs, e monta tudo sozinho. Isso foi uma exigência do projeto
(rodar no GitHub Pages só abrindo o `index.html`) e tem uma vantagem didática: dá para ler o código de
ponta a ponta sem ferramentas intermediárias.

```
  Python (pipeline/)                         Navegador
  ─────────────────                         ─────────────────────────────────────────────
  dados brutos ──► análise ──► preparar_site.py ──► json/*.json ──► main.js ──► capN.js ──► SVG
                                                                      │
                                                     preencher() ◄────┘  (cifras do texto)
```

A regra que organiza tudo: **o navegador não calcula estatística**. Toda conta pesada é feita em
Python, uma vez, e o site só lê números prontos. O JavaScript cuida de desenhar, animar e responder
ao leitor.

## 1.2 Bibliotecas (todas por CDN, com versão fixa)

| Biblioteca | Versão | Para quê | Onde |
|---|---|---|---|
| [D3.js](https://d3js.org) | 7.9.0 | Escalas, eixos, formas (linhas, áreas), projeção de mapa, transições, pincel (*brush*), simulação de forças | todos os capítulos |
| [Scrollama](https://github.com/russellsamora/scrollama) | 3.2.0 | Detecta qual "passo" de texto está no meio da tela e o progresso dentro dele | `util.js` → `scrolly()` |
| [noUiSlider](https://refreshless.com/nouislider/) | 15.7.1 | Sliders de faixa com duas alças, acessíveis por teclado | capítulo 7 (filtros) |
| [Tom Select](https://tom-select.js.org) | 2.3.1 | Campo de busca com sugestões e acentos ignorados | capítulo 7 (busca) |
| Google Fonts | — | Fraunces (títulos) e Source Sans 3 (texto e números) | `index.html` |

**Por que versão fixa?** Uma CDN com `d3@7` (sem o número completo) pode entregar uma versão nova
amanhã e quebrar o site sem que ninguém tenha mudado nada. Com `7.9.0`, o site de hoje continua igual.

## 1.3 Os arquivos JavaScript

Os scripts são **módulos ES** (`<script type="module">`): cada arquivo declara o que exporta
(`export function initCap1…`) e o que importa (`import { fmt } from "./util.js"`). D3, Scrollama,
noUiSlider e Tom Select chegam como **globais** (`window.d3` etc.), carregados antes por `<script>` comum.

| Arquivo | Responsabilidade |
|---|---|
| `main.js` | Carrega os JSONs, preenche as cifras do texto, inicia os capítulos. Os capítulos 4, 5 e 7 são iniciados **quando o navegador está ocioso** (ou quando o leitor se aproxima deles) |
| `util.js` | Formatação em pt-BR, `preencher()`, cores validadas, escala de cobertura, tooltip, `scrolly()`, `aoRedimensionar()` |
| `cap1.js` | Linha da cobertura acumulada (desenhada pela rolagem), faixa P10–P90, calendário de doses diárias |
| `cap2.js` | Dispersão com troca do eixo X a cada suspeito e o carimbo "descartado" |
| `cap3.js` | Mapa que se corrige com a rolagem (estimativa 2021 → Censo → pessoas) e o contador |
| `cap4.js` | Pontos que voam da dispersão para o mapa, os 13 por perfil, funil e os três mapas com o I de Moran |
| `cap5.js` | Enxame (*beeswarm*) do reforço e dispersão voto × reforço |
| `cap7.js` | Explore: mapa, dispersão, coordenadas paralelas, filtros, busca, detalhe e tabela coordenados |

## 1.4 Padrões que se repetem (vale estudar com calma)

### a) Cifras do texto vêm dos dados, nunca digitadas

No HTML, um número aparece assim:

```html
<span data-v="cap3.contagens.b"></span> municípios acima de 100%
```

`preencher()` (em `util.js`) percorre todos os `[data-v]`, busca o caminho no objeto de dados
(`cap3 → contagens → b`) e escreve o valor formatado (`data-f="pct"`, `"int"`, `"rho"`…). Se o caminho
não existir, aparece `{{TODO: …}}` em amarelo — impossível publicar um número inventado sem perceber.
Consequência prática: **se a análise mudar, basta rodar `preparar_site.py`; o texto se atualiza sozinho.**

### b) Um SVG por gráfico, reutilizado entre os passos

Cada gráfico cria seu `<svg>` uma vez. Os passos da rolagem só mudam atributos (posição, cor,
opacidade). Criar e destruir elementos a cada passo seria lento e impediria transições suaves.
O mecanismo do D3 para isso é o **data join**:

```js
selecao.data(dados, (d) => d.id)   // a chave liga cada elemento ao mesmo município sempre
  .join(entra => ..., atualiza => ..., sai => ...)
```

A **chave** (`d => d.id`) é o que permite a "transição-assinatura" do capítulo 4: o mesmo círculo de
Fortaleza que estava na dispersão é o que voa para Fortaleza no mapa.

### c) Scrollytelling com Scrollama: degrau e progresso

`scrolly()` (em `util.js`) recebe dois retornos:
- `onPasso(i)` — dispara quando o passo *i* cruza a linha de referência (60% da altura da tela).
  Bom para mudanças discretas: trocar o eixo da dispersão, carimbar, mudar de vista.
- `onProgresso(i, p)` — dispara continuamente com `p` de 0 a 1 enquanto o passo atravessa a tela.
  Bom para estados contínuos: a linha que se desenha (capítulo 1) e o mapa que se corrige (capítulo 3).

O capítulo 3 **interpola** o valor de cada município entre dois estados: `lerp(a, b, t)`. Por isso o
contador passa por números intermediários (37 → … 53 … → 60): ele conta, a cada quadro, quantos
municípios estão acima de 100% naquele instante da transição.

Dois cuidados implementados:
- **Sem sequestro de rolagem** (*scroll-jacking*): a página rola normalmente; o gráfico só reage.
- **Um redesenho por quadro**: o Scrollama pode disparar vários eventos de progresso entre dois quadros
  da tela. `scrolly()` agrupa todos num único `requestAnimationFrame`.

### d) Gráfico fixo com `position: sticky`

O gráfico fica preso na tela (`.sticky`) enquanto os passos de texto rolam ao lado (desktop) ou por
cima (celular, abaixo de 860 px). No celular, o gráfico ocupa a metade de cima e o texto passa pela de
baixo, para não cobrir os dados.

### e) Responsividade sem recarregar

`aoRedimensionar(fn)` usa um `ResizeObserver` (com espera de 120 ms) para recalcular escalas e
redesenhar quando o contêiner muda de tamanho — inclusive ao girar o celular.

### f) Estado único no Explore (capítulo 7)

Todas as visões leem o mesmo objeto:

```js
const estado = { sel: null, filtros: {}, x: "renda" };
```

Qualquer interação altera o estado e chama `emitir()`, que redesenha **todas** as visões
(mapa, dispersão, paralelas, detalhe, tabela, histogramas). É o padrão de **visões coordenadas**: não
há visão que "manda" na outra; todas obedecem ao estado. O pincel das paralelas e os sliders se
sincronizam nos dois sentidos com uma trava (`movendo`, `externo`) para não entrarem em laço.

## 1.5 Animação e movimento reduzido

- Transições de 600–900 ms com `d3.easeCubicInOut`; entradas escalonadas (`.delay(...)`) nos pontos.
- Números que contam até o valor final (`contar()`, usa `IntersectionObserver` para só começar quando
  aparecem na tela).
- `prefers-reduced-motion: reduce` (configuração do sistema operacional): `DUR` vira 0 e cada passo vai
  direto ao estado final. Isso é acessibilidade, não detalhe: animações podem causar enjoo em
  pessoas com distúrbios vestibulares.

## 1.6 Acessibilidade

| Recurso | Como |
|---|---|
| Texto alternativo | Cada `<svg>` tem `role="img"`, `<title>` e `<desc>` com os números principais |
| Teclado | Mapa e dispersão do Explore recebem foco; setas percorrem municípios, Esc limpa. Sliders: setas, PageUp/PageDown, Home/End |
| Leitor de tela | Seleções anunciadas em `aria-live`; sliders com `aria-label` e valor formatado |
| Alternativa aos gráficos | Tabela completa e ordenável no capítulo 7 |
| Cor nunca sozinha | Perfis do capítulo 4 têm forma (círculo, quadrado, losango) além de cor; alertas têm contorno e ▲ |
| Contraste | Todos os tons de texto ≥ 4,5:1 sobre o fundo (WCAG 2 AA) |
| Atalhos | "Pular para o conteúdo" e link direto para o Explore na abertura |

## 1.7 Desempenho (medido)

Medição com `testes/desempenho.mjs` rolando a página inteira:

| Cenário | fps mediano | fps no pior 5% | tarefas longas | maior tarefa |
|---|---|---|---|---|
| Desktop 1366 px | ~60 | ~44–50 | 0 | — |
| Celular 360 px, CPU 4× mais lenta | ~59 | ~27–35 | 2–7 | ~60 ms |

O que foi otimizado na revisão: um redesenho por quadro na rolagem; caminhos do mapa calculados uma
vez por tamanho de tela (cache); capítulos pesados iniciados quando o navegador está ocioso; malha com
coordenadas em 3 casas decimais (~110 m, abaixo de 1 pixel na tela). Total transferido: ~0,9 MB
(sem compressão; o GitHub Pages comprime).

## 1.8 Testes no navegador

A pasta `testes/` (só local, fora do GitHub) tem roteiros que abrem o site num Chrome invisível (*headless*) com
[Puppeteer](https://pptr.dev), rolam até cada passo, clicam, digitam e tiram capturas de tela.

```bash
python -m http.server 8000            # num terminal
cd testes && npm install              # uma vez
npm run passos            # rola por todos os passos (desktop); acusa erros de console e {{TODO}}
npm run passos:celular
npm run explore           # busca, eixo X, pincel, sliders por teclado, setas no mapa, tabela
npm run desempenho:celular
```

Variáveis: `CHROME` (caminho do navegador) e `URL` (endereço do site). As cifras são auditadas à parte,
em Python: `python pipeline/auditar_cifras.py`.

Lição aprendida nos testes: uma captura de tela no meio de uma interação tira o foco da página e fecha
listas abertas; e a rolagem suave (`scroll-behavior: smooth`) faz cliques automáticos caírem no lugar
errado. Por isso os testes desligam a rolagem suave e só capturam a tela ao final.

## 1.9 Como mexer

- **Mudar um texto:** edite `index.html`. Números sempre via `data-v`.
- **Mudar um número:** mude a análise, rode `pipeline/preparar_site.py` e `pipeline/auditar_cifras.py`.
- **Novo gráfico:** crie a função no `capN.js` do capítulo (padrão: `layout()` calcula escalas e chama
  `desenhar()`; `aoRedimensionar(layout).observe(container)`), e o JSON correspondente em
  `preparar_site.py`.
- **Nova cor:** valide antes (ver [03-tipos-de-dados.md](03-tipos-de-dados.md#36-cor)).

## 1.10 Publicação no GitHub Pages

1. Faça *commit* de `index.html`, `css/`, `js/`, `json/` (e do resto, se quiser o projeto completo).
2. *Settings → Pages → Build and deployment → Deploy from a branch → main → / (root)*.
3. Em ~1 minuto o site fica em `https://<usuário>.github.io/<repositório>/`.

O projeto não usa Git LFS: o maior arquivo enviado tem menos de 20 MB. O que não vai para o GitHub está
no `.gitignore`, principalmente os microdados (`dados/brutos/microdados_CE/`, 491 MB), dos quais o site
não depende.

## Perguntas de revisão

1. Por que o site não calcula correlações no navegador?
2. O que aconteceria com a transição dispersão → mapa se o `data()` não tivesse a chave `d => d.id`?
3. Qual a diferença entre `onPasso` e `onProgresso` e quando usar cada um?
4. Por que o contador do capítulo 3 passa por números como 53, que não aparecem em nenhum estado?
5. Como o capítulo 7 evita que o pincel e o slider fiquem se atualizando um ao outro em laço?
6. Cite três decisões de acessibilidade e o problema que cada uma resolve.
7. Por que `overflow-x: clip` e não `overflow-x: hidden` no `body`? (Dica: `position: sticky`.)
