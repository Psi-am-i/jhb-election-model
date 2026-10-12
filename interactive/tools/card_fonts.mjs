#!/usr/bin/env node
// The share cards' fonts (interactive/js/share-card.js): IBM Plex, the site's
// own Latin-1 subsets as TrueType in src/card-fonts/ (README there), which the
// site's Worker hands to resvg for link previews (src/og-render.js). The card
// lays its text out by these faces' advance widths, read here from the fonts'
// own cmap and hmtx tables and written to interactive/js/card-fonts.js, so a
// headline is measured with the font that draws it.
//
//   node interactive/tools/card_fonts.mjs          write interactive/js/card-fonts.js
//   node interactive/tools/card_fonts.mjs --check  exit 1 if it differs from the fonts
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { advanceMap } from "../../worker-api/tools/font_widths.mjs";

const here = dirname(fileURLToPath(import.meta.url));
export const REPO = resolve(here, "../..");
export const FONT_DIR = resolve(REPO, "src/card-fonts");
export const OUT = resolve(REPO, "interactive/js/card-fonts.js");

// face key -> [file, CSS family, weight]. src/og-render.js bundles exactly
// these files; the card names the families and weights.
export const FACES = {
  sans: ["IBMPlexSans-Regular-Latin1.ttf", "IBM Plex Sans", 400],
  sansSemi: ["IBMPlexSans-SemiBold-Latin1.ttf", "IBM Plex Sans", 600],
  sansBold: ["IBMPlexSans-Bold-Latin1.ttf", "IBM Plex Sans", 700],
  serifSemi: ["IBMPlexSerif-SemiBold-Latin1.ttf", "IBM Plex Serif", 600],
  monoSemi: ["IBMPlexMono-SemiBold-Latin1.ttf", "IBM Plex Mono", 600],
};

export function render() {
  const lines = Object.entries(FACES).map(([k, [file, family, weight]]) => {
    const { em, w } = advanceMap(readFileSync(resolve(FONT_DIR, file)));
    const pairs = Object.entries(w).map(([c, v]) => `${c}:${v}`).join(",");
    return `  ${k}: { family: "${family}", weight: ${weight}, em: ${em}, w: {${pairs}} },`;
  });
  return `// Written by interactive/tools/card_fonts.mjs from src/card-fonts/. Do not edit.
// Advance widths, in font units, of every character each face carries.
export const FACES = {
${lines.join("\n")}
};
`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const want = render();
  if (process.argv.includes("--check")) {
    let have = "";
    try { have = readFileSync(OUT, "utf8"); } catch { /* missing */ }
    if (have !== want) { console.error("interactive/js/card-fonts.js is stale: run node interactive/tools/card_fonts.mjs"); process.exit(1); }
    console.log("interactive/js/card-fonts.js matches src/card-fonts/");
  } else {
    writeFileSync(OUT, want);
    console.log("wrote interactive/js/card-fonts.js");
  }
}
