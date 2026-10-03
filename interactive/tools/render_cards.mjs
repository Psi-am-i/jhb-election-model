#!/usr/bin/env node
// The share cards as the edge draws them: share-card.js's SVG, rasterised by
// resvg-wasm with src/card-fonts/ (src/og-raster.js, the call src/og-render.js
// makes in the Worker), for the two forecasts of interactive/tests/
// share-fixture.json. Writes interactive/screenshots/share-card-link.png,
// share-card-story.png and share-duel.png, or the directory given.
//
//   node interactive/tools/render_cards.mjs [out-dir]
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { initWasm, Resvg } from "../../worker-api/node_modules/@resvg/resvg-wasm/index.mjs";
import { rasterise } from "../../src/og-raster.js";
import * as SC from "../js/share-card.js";
import { FACES } from "./card_fonts.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(here, "../..");
export const FIXTURE = JSON.parse(readFileSync(resolve(REPO, "interactive/tests/share-fixture.json"), "utf8"));

let ready;
export async function toPNG(svg) {
  ready ??= initWasm(readFileSync(resolve(REPO, "worker-api/node_modules/@resvg/resvg-wasm/index_bg.wasm")));
  await ready;
  const fonts = Object.values(FACES).map(([file]) => readFileSync(resolve(REPO, "src/card-fonts", file)));
  return rasterise(Resvg, svg, fonts);
}

export function assets(F = FIXTURE) {
  const logos = {};
  const have = new Set(readdirSync(resolve(REPO, "site/logos")));
  for (const [c, p] of Object.entries(F.parties)) {
    if (p.logo && have.has(c + ".png")) logos[c] = "data:image/png;base64," + readFileSync(resolve(REPO, "site/logos", c + ".png")).toString("base64");
  }
  return { logos, brand: SC.brandOf(readFileSync(resolve(REPO, "site/logo.svg"), "utf8")), geom: F.geometry };
}

// A fixed sealing instant for the pictures: noon in Johannesburg, 3 October 2026.
export const MADE = { at: Date.parse("2026-10-03T10:05:00Z"), sealed: true };

export function specs(F = FIXTURE, made = MADE) {
  const party = c => F.parties[c];
  const one = X => SC.forecastSpec({ name: X.name, answer: X.answer, outcome: X.answer.outcome, vote: X.vote,
    calls: X.calls, party, baseline: F.baseline, election: F.election, made });
  return { party, A: one(F.A), B: one(F.B) };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const out = resolve(process.argv[2] || resolve(REPO, "interactive/screenshots"));
  mkdirSync(out, { recursive: true });
  const { party, A, B } = specs();
  const a = assets();
  const jobs = [["share-card-link.png", SC.linkCardSVG(A, a, party)], ["share-card-story.png", SC.storyCardSVG(A, a, party)],
    ["share-duel.png", SC.duelCardSVG(A, B, a, party)], ["share-card-link-B.png", SC.linkCardSVG(B, a, party)]];
  for (const [name, svg] of jobs) {
    writeFileSync(resolve(out, name), await toPNG(svg));
    console.log("wrote", resolve(out, name));
  }
}
