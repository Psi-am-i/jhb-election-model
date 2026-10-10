// One SVG card to PNG bytes under node: resvg-wasm from worker-api/node_modules
// and the card faces from src/card-fonts/, through src/og-raster.js (the call
// the Worker makes in src/og-render.js). It loads no fixture, so the site
// build (src/og-pages.mjs) and the share-card tools
// (interactive/tools/render_cards.mjs, which re-exports it) share this one
// definition. `npm ci` in worker-api/ is its prerequisite.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { initWasm, Resvg } from "../worker-api/node_modules/@resvg/resvg-wasm/index.mjs";
import { rasterise } from "./og-raster.js";
import { FACES } from "../interactive/tools/card_fonts.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");

let ready;
export async function toPNG(svg) {
  ready ??= initWasm(readFileSync(resolve(REPO, "worker-api/node_modules/@resvg/resvg-wasm/index_bg.wasm")));
  await ready;
  const fonts = Object.values(FACES).map(([file]) => readFileSync(resolve(REPO, "src/card-fonts", file)));
  return rasterise(Resvg, svg, fonts);
}
