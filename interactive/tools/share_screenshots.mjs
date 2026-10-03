// Screenshots of sharing a reader's forecast (audits/2026-10-03-share-design):
// the arrival view a shared link opens, at 375 and 1440 wide; the return
// card's share sheet after starting from the friend's forecast; and the three
// cards as the edge draws them (render_cards.mjs). Into <out>/share-*.png.
//
//   build the site into a scratch directory with site/draws and site/logos
//   linked beside it (interactive/README.md), then
//     PLAYWRIGHT=<playwright or playwright-core index.mjs> YF_ROOT=<scratch site> \
//       node interactive/tools/share_screenshots.mjs interactive/screenshots
//
// The browser is served by the tool itself (no port). The site's Worker is
// stood in for by this tool for the two seal routes only, with src/seal.js
// and a key made up for the pictures: the link is the share fixture's first
// forecast (interactive/tests/share-fixture.json), sealed at a fixed time.
// Pyodide loads from cdn.jsdelivr.net. Any page error is printed at the end.
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, extname, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as B from "../js/builder-state.js";
import * as MS from "../js/make-state.js";
import { makeSeal, checkSeal } from "../../src/seal.js";
import { FIXTURE, MADE, specs, assets, toPNG } from "./render_cards.mjs";
import * as SC from "../js/share-card.js";
import { writeFileSync } from "node:fs";

const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const OUT = resolve(process.argv[2] || "interactive/screenshots");
const ROOT = process.env.YF_ROOT;
if (!ROOT) throw new Error("set YF_ROOT to a built site");
const ORIGIN = "http://127.0.0.1:8801";
const KEY = "screenshot-only-key";
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".bin": "application/octet-stream",
  ".py": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2" };

// the link: the fixture's first forecast, against the built page's context
const D = JSON.parse(readFileSync(join(ROOT, "your-forecast/forecast.json"), "utf8"));
const ctx = B.contextOf(D.schema);
const st = B.startState(ctx, { calls: FIXTURE.A.calls, share: FIXTURE.A.vote }, FIXTURE.A.calls).state;
const fields = { v: MS.FORMAT, c: D.context_ref, f: MS.encode(st, FIXTURE.A.coalition, ctx), n: FIXTURE.A.name };
const s = await makeSeal(KEY, fields, MADE.at);
const LINK = ORIGIN + "/your-forecast/?" + new URLSearchParams({ ...fields, s, from: "1" }).toString();

const b = await chromium.launch();
const errors = [];

async function open(w, h, url) {
  const c = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1, colorScheme: "dark" });
  await c.route(ORIGIN + "/**", async route => {
    const req = route.request();
    const p = decodeURIComponent(new URL(req.url()).pathname);
    if (p === "/seal/1/check" || p === "/seal/1") {
      const body = JSON.parse(req.postData() || "{}");
      const f = { v: body.v, c: body.c, f: body.f, n: body.n };
      const out = p === "/seal/1" ? { s: await makeSeal(KEY, f, MADE.at + 3600e3) }
        : await checkSeal(KEY, f, body.s).then(r => ({ sealed: r.sealed, at: r.sealed ? new Date(r.at).toISOString() : null }));
      return route.fulfill({ status: 200, body: JSON.stringify(out), contentType: "application/json" });
    }
    const f = join(ROOT, p.endsWith("/") ? p + "index.html" : p);
    if (!existsSync(f) || statSync(f).isDirectory()) return route.fulfill({ status: 404, body: "missing" });
    return route.fulfill({ status: 200, body: readFileSync(f), contentType: TYPES[extname(f)] || "application/octet-stream" });
  });
  const pg = await c.newPage();
  pg.on("pageerror", e => errors.push(`${w}: ${e.message}`));
  // pin the page's clock to the sealing time's day, so the countdown matches the cards
  await pg.addInitScript(t => { const real = Date.now; const off = t - real(); Date.now = () => real() + off; }, MADE.at + 7200e3);
  await pg.goto(url, { waitUntil: "load" });
  return pg;
}

for (const [w, h] of [[375, 812], [1440, 1000]]) {
  const pg = await open(w, h, LINK);
  await pg.waitForFunction(() => document.querySelector('[data-live="arrival"] .yf-arr-chance') &&
    document.querySelector('[data-live="arrival"] .yf-arr-seal')?.dataset.seal === "sealed", null, { timeout: 300000 });
  await pg.waitForTimeout(400);
  // the page from its top to the end of the arrival view
  const bottom = await pg.evaluate(() => Math.ceil(document.querySelector('[data-live="arrival"]').getBoundingClientRect().bottom + scrollY + 24));
  await pg.screenshot({ path: `${OUT}/share-arrival-${w}.png`, fullPage: true, clip: { x: 0, y: 0, width: w, height: bottom } });
  if (w === 1440) {
    // start from the friend's forecast, open the share sheet, pick both forecasts
    await pg.click('[data-live="arrival"] .yf-arr-btns .btn.primary');
    await pg.waitForFunction(() => !document.querySelector('[data-live="b-share"] .shareopen').disabled, null, { timeout: 120000 });
    await pg.click('[data-live="b-share"] .shareopen');
    await pg.fill('[data-live="b-share"] .shname', "Kgomotso");
    await pg.waitForFunction(() => !document.querySelector('[data-live="b-share"] .shduel').hidden, null, { timeout: 120000 });
    await pg.selectOption('[data-live="b-share"] .shimg', "duel");
    await pg.waitForFunction(() => { const i = document.querySelector('[data-live="b-share"] .preview img');
      return i.src.startsWith("blob:") && i.complete && i.naturalWidth > 0 && /Kgomotso/.test(i.alt); }, null, { timeout: 120000 });
    await pg.waitForFunction(() => /^Sealed/.test(document.querySelector('[data-live="b-share"] .shseal').textContent), null, { timeout: 30000 });
    await pg.waitForTimeout(300);
    await pg.screenshot({ path: `${OUT}/share-sheet-duel.png` });
  }
  await pg.context().close();
}
await b.close();

// the cards, as the edge draws them
const { party, A, B: Bs } = specs();
const a = assets();
for (const [name, svg] of [["share-card-link.png", SC.linkCardSVG(A, a, party)], ["share-card-story.png", SC.storyCardSVG(A, a, party)],
  ["share-duel.png", SC.duelCardSVG(A, Bs, a, party)]]) writeFileSync(join(OUT, name), await toPNG(svg));

console.log("wrote share-arrival-375.png, share-arrival-1440.png, share-sheet-duel.png, share-card-link.png, share-card-story.png, share-duel.png");
if (errors.length) { console.error("page errors:\n" + errors.join("\n")); process.exitCode = 1; }
