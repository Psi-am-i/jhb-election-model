// Screenshots of the built /your-forecast/ page into interactive/screenshots/yf-*.png.
//
//   build the site into a scratch directory, link site/share.jpg, site/logos
//   and site/draws beside it, then either serve it on 127.0.0.1:8801 or let
//   this tool serve it to the browser itself (no port):
//     PLAYWRIGHT=<playwright or playwright-core index.mjs> \
//       YF_ROOT=<the scratch site directory> \
//       node interactive/tools/yf_screenshots.mjs interactive/screenshots
//
// States (owner's sweep, 2026-10-03): section 1 adjusted (Black African
// turnout +5) at 375 and 1440, first screen and whole page; section 1 under
// Germany's 2023 law, sharing refused; section 2's walkthrough, step one
// highlighted, opened from section 1's adjusted forecast; the analysis, with
// a ward's chance on hover; both share images, at both sizes for section 1;
// the phone's change toast with the seat table out of view; an old /make/
// link restored. Pyodide loads from cdn.jsdelivr.net. Any page error is
// printed at the end.
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const OUT = process.argv[2];
const ROOT = process.env.YF_ROOT;
const ORIGIN = "http://127.0.0.1:8801";
const BASE = ORIGIN + "/your-forecast/";
const BA5 = "?t=5,0,0,0";
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".bin": "application/octet-stream",
  ".py": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2" };

const b = await chromium.launch();
const errors = [];

async function page(w, h, query, { wait = "adjust" } = {}) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1,
                                   colorScheme: "dark", acceptDownloads: true });
  if (ROOT) await ctx.route(ORIGIN + "/**", route => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname);
    if (p.endsWith("/")) p += "index.html";
    const f = join(ROOT, p);
    if (!existsSync(f) || statSync(f).isDirectory()) return route.fulfill({ status: 404, body: "missing" });
    return route.fulfill({ status: 200, body: readFileSync(f), contentType: TYPES[extname(f)] || "application/octet-stream" });
  });
  const p = await ctx.newPage();
  p.on("pageerror", e => errors.push(`${w} ${query}: ${e.message}`));
  await p.goto(BASE + query, { waitUntil: "load" });
  await p.waitForFunction(() => document.querySelector('[data-live="engine"]').hasAttribute("data-ready"), null, { timeout: 180000 });
  if (wait === "adjust" && query) await p.waitForFunction(() => document.querySelector('[data-live="seats"] .st-row'), null, { timeout: 120000 });
  await p.waitForTimeout(600);
  return p;
}
const breakReady = p => p.waitForFunction(() => document.querySelector('[data-live="b-council"] .bars .st-row')
  && !document.querySelector('[data-live="b-actions"] .yf-analyse').disabled, null, { timeout: 240000 });
const imgReady = sel => p => p.waitForFunction(s => { const i = document.querySelector(s); return i.src.startsWith("blob:") && i.complete && i.naturalWidth > 0; },
  sel, { timeout: 60000 });
const download = async (p, sel, path) => { const d = p.waitForEvent("download"); await p.click(sel); await (await d).saveAs(path); };

for (const [w, h] of [[375, 812], [1440, 1000]]) {
  // section 1, adjusted
  let p = await page(w, h, BA5);
  await p.screenshot({ path: `${OUT}/yf-adjust-${w}-fold.png` });
  await p.screenshot({ path: `${OUT}/yf-adjust-${w}.png`, fullPage: true });
  // its share sheet and image (1440 only: the image is the same at any width)
  if (w === 1440) {
    await p.click('[data-live="share"] .pl-shareopen');
    await imgReady('[data-live="share"] .preview img')(p);
    await p.fill('[data-live="share"] .pl-name', "Thandi");
    await p.waitForFunction(() => /Thandi/.test(document.querySelector('[data-live="share"] .preview img').alt), null, { timeout: 30000 });
    await imgReady('[data-live="share"] .preview img')(p);
    await p.waitForTimeout(300);
    await p.screenshot({ path: `${OUT}/yf-adjust-share.png` });
    await download(p, '[data-live="share"] .shdl', `${OUT}/yf-card-adjust-1200x630.png`);
    await p.click('[data-live="share"] .sizes button[data-size="story"]');
    await p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.naturalHeight > i.naturalWidth; }, null, { timeout: 30000 });
    await download(p, '[data-live="share"] .shdl', `${OUT}/yf-card-adjust-1080x1920.png`);
    await p.click('[data-live="share"] .x');
  }
  // section 2 opened from it: the walkthrough, step one highlighted
  await p.locator("#break").scrollIntoViewIfNeeded();
  await breakReady(p);
  await p.locator("#h-break").evaluate(e => e.scrollIntoView({ block: "start" }));
  await p.waitForTimeout(500);
  await p.screenshot({ path: `${OUT}/yf-break-${w}.png` });
  // a few wards changed, step two highlighted: the brush on the party
  // alphabetically first that the start calls for no ward, three wards
  // given to it
  const spare = await p.evaluate(() => {
    const opts = [...document.querySelectorAll('[data-live="b-map"] .brushselect option')].filter(o => o.value);
    const held = new Set([...document.querySelectorAll('[data-live="b-map"] .brushscroll button')].map(b => b.value));
    return opts.find(o => !held.has(o.value)).value;
  });
  await p.selectOption('[data-live="b-map"] .brushselect', spare);
  // by keyboard (focus, Enter): on a phone the brush tray covers part of the map
  for (const k of [12, 70, 130]) {
    await p.locator('[data-live="b-map"] svg .w').nth(k).focus();
    await p.keyboard.press("Enter");
  }
  await p.waitForFunction(() => /changed/.test(document.querySelector('[data-live="b-map"] .nchanged').textContent), null, { timeout: 30000 });
  await p.locator("#h-break").evaluate(e => e.scrollIntoView({ block: "start" }));
  await p.click('[data-live="b-map"] .yf-next');
  await p.waitForTimeout(500);
  await p.screenshot({ path: `${OUT}/yf-break-${w}-step2.png` });
  // the analysis
  await p.click('[data-live="b-actions"] .yf-analyse');
  await p.waitForFunction(() => document.querySelector('[data-live="b-analysis"] tbody tr'), null, { timeout: 60000 });
  await p.waitForTimeout(700);
  await p.screenshot({ path: `${OUT}/yf-analyse-${w}.png` });
  if (w === 1440) {
    // a ward's chance, on hover over section 2's map
    const ward = p.locator('[data-live="b-map"] svg .w').nth(40);
    await ward.scrollIntoViewIfNeeded();
    await ward.hover();
    await p.waitForTimeout(300);
    await p.screenshot({ path: `${OUT}/yf-analyse-hover.png` });
    // section 2's share image
    await p.click('[data-live="b-share"] .shareopen');
    await imgReady('[data-live="b-share"] .preview img')(p);
    await p.waitForTimeout(300);
    await p.screenshot({ path: `${OUT}/yf-break-share.png` });
    await download(p, '[data-live="b-share"] .shdl', `${OUT}/yf-card-break-1200x630.png`);
  }
  await p.context().close();
}

// the phone: a lever moved with the seat table out of view gives the toast
{
  const p = await page(375, 812, BA5);
  await p.locator("#h-bye").scrollIntoViewIfNeeded();
  await p.waitForTimeout(400);
  await p.evaluate(() => { const i = document.querySelectorAll('[data-live="turnout"] input')[3]; i.value = "-3"; i.dispatchEvent(new Event("input", { bubbles: true })); });
  await p.waitForFunction(() => !document.querySelector('[data-live="toast"]').hidden, null, { timeout: 60000 });
  await p.waitForTimeout(250);
  await p.screenshot({ path: `${OUT}/yf-phone-toast-375.png` });
  await p.context().close();
}
// Germany's 2023 law: sharing refused, and said why
{
  const p = await page(1440, 1000, "?l=cap");
  await p.locator("#h-law").scrollIntoViewIfNeeded();
  await p.waitForTimeout(300);
  console.log("share under cap:", await p.evaluate(() => [document.querySelector('[data-live="share"] .pl-shareopen').disabled,
    document.querySelector('[data-live="share"] .pl-sharewhy').textContent]));
  await p.screenshot({ path: `${OUT}/yf-adjust-1440-law.png` });
  await p.context().close();
}
await b.close();
console.log(errors.length ? errors.join("\n") : "no page errors");
