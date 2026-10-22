// One SVG card to PNG bytes with resvg, the card's own fonts and no system
// font: the call src/og-render.js makes at the edge, and
// interactive/tools/render_cards.mjs makes under node with the same files.
// No imports, so node can load it without the Worker's wasm and font modules.

export function rasterise(ResvgClass, svg, fonts) {
  const r = new ResvgClass(svg, {
    font: {
      fontBuffers: fonts.map(b => new Uint8Array(b)),
      loadSystemFonts: false,
      defaultFontFamily: "IBM Plex Sans",
      sansSerifFamily: "IBM Plex Sans",
      serifFamily: "IBM Plex Serif",
      monospaceFamily: "IBM Plex Mono",
    },
    fitTo: { mode: "original" },
  });
  try {
    const img = r.render();
    try { return img.asPng(); } finally { img.free(); }
  } finally { r.free(); }
}
