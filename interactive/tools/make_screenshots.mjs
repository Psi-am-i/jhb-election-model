// Screenshots of the built /make/ page into interactive/screenshots/make-*.png.
//   build the site into a scratch directory, copy site/share.jpg, site/logos
//   and site/draws beside it, serve it on 127.0.0.1:8801, then
//   PLAYWRIGHT=<path to playwright/index.mjs> node interactive/tools/make_screenshots.mjs interactive/screenshots
const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const OUT = process.argv[2];
const BASE = "http://127.0.0.1:8801/make/";
const b = await chromium.launch();
const errors = [];
const ready = p => p.waitForFunction(() => document.querySelector('[data-live="council"] .bars .bar'), null, { timeout: 180000 });

async function page(w, h, query = "") {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1, colorScheme: "dark", acceptDownloads: true });
  const p = await ctx.newPage();
  p.on("pageerror", e => errors.push(w + " " + query + ": " + e.message));
  await p.goto(BASE + query, { waitUntil: "load" });
  await ready(p);
  await p.waitForTimeout(400);
  return p;
}

// The reader's edits: five wards to the DA, the ANC to 20%, a DA + ActionSA coalition.
async function edit(p) {
  await p.selectOption('[data-live="map"] .brushselect', "DA");
  for (const i of [0, 1, 2, 3, 4]) {
    await p.locator('[data-live="map"] svg .w').nth(i).dispatchEvent("pointerdown", { pointerType: "mouse", bubbles: true });
  }
  await p.evaluate(() => window.dispatchEvent(new PointerEvent("pointerup", { pointerType: "mouse" })));
  await p.fill("#pr-n-ANC", "20");
  await p.locator("#pr-n-ANC").dispatchEvent("change");
  await p.waitForTimeout(300);
  for (const n of ["DA", "ActionSA"]) await p.locator('[data-live="govern"] .coal .chip', { hasText: n }).first().click();
  await p.waitForTimeout(400);
}

const links = {};
for (const [w, h] of [[375, 812], [1440, 1000]]) {
  let p = await page(w, h);
  await p.screenshot({ path: OUT + "/make-" + w + "-default.png", fullPage: true });
  await edit(p);
  links[w] = await p.evaluate(() => location.search);
  await p.screenshot({ path: OUT + "/make-" + w + "-edited.png", fullPage: w > 500 });
  if (w < 500) {
    await p.locator('[data-live="council"]').scrollIntoViewIfNeeded();
    await p.screenshot({ path: OUT + "/make-375-edited-council.png" });
  }
  await p.click('[data-live="share"] .shareopen');
  await p.fill('[data-live="share"] .shname', "Thandi");
  await p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.src.startsWith("blob:") && i.complete && i.naturalWidth > 0 && /Thandi/.test(i.alt); }, null, { timeout: 30000 });
  await p.waitForTimeout(400);
  await p.screenshot({ path: OUT + "/make-" + w + "-share.png" });
  if (w > 500) {
    const d = p.waitForEvent("download");
    await p.click('[data-live="share"] .shdl');
    await (await d).saveAs(OUT + "/make-card-1200x630.png");
    links.named = await p.evaluate(() => location.search);
  }
  await p.context().close();
}
// a link restores exactly
const p = await page(1440, 1000, links.named);
console.log("restored:", await p.evaluate(() => location.search) === links.named);
await p.context().close();
// an invalid link falls back, visibly
const q = await page(1440, 1000, "?v=1&c=000000000000&f=AAAA");
console.log("invalid-link note:", await q.evaluate(() => document.querySelector('[data-live="status"] .linknote').textContent));
await q.screenshot({ path: OUT + "/make-1440-invalid-link.png" });
await b.close();
console.log("link length:", links.named.length, links.named);
console.log(errors.length ? errors.join("\n") : "no page errors");
