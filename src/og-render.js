// The link preview's rasteriser: an SVG card (interactive/js/share-card.js)
// to PNG, with resvg-wasm and the card's own IBM Plex faces (src/card-fonts/,
// README there). src/worker.js reaches this module only through a dynamic
// import inside its /og/ route, so the rest of the site never loads it and a
// failure here costs a preview, never a page: the route answers its fallback.
//
// resvg-wasm is worker-api's pinned dependency (worker-api/package.json,
// 2.6.2), imported by path: the repository root has no package.json. Run
// `npm ci` in worker-api/ before `wrangler deploy` at the root. The .wasm
// import is compiled by wrangler at upload (a Worker may not compile wasm
// from bytes at run time); the .ttf imports are Data modules
// (wrangler.toml [[rules]]).

import { initWasm, Resvg } from "../worker-api/node_modules/@resvg/resvg-wasm/index.mjs";
import resvgWasm from "../worker-api/node_modules/@resvg/resvg-wasm/index_bg.wasm";
import sans from "./card-fonts/IBMPlexSans-Regular-Latin1.ttf";
import sansSemi from "./card-fonts/IBMPlexSans-SemiBold-Latin1.ttf";
import sansBold from "./card-fonts/IBMPlexSans-Bold-Latin1.ttf";
import serifSemi from "./card-fonts/IBMPlexSerif-SemiBold-Latin1.ttf";
import monoSemi from "./card-fonts/IBMPlexMono-SemiBold-Latin1.ttf";
import { rasterise } from "./og-raster.js";

export const FONTS = [sans, sansSemi, sansBold, serifSemi, monoSemi];

// Initialised once per isolate: a compiled module, not a request's data.
let ready;
export async function renderPNG(svg) {
  ready ??= initWasm(resvgWasm);
  await ready;
  return rasterise(Resvg, svg, FONTS);
}
