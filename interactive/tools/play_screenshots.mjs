// Screenshots of the built /play/ page into interactive/screenshots/play-*.png.
//   build the site, serve site/ on 127.0.0.1:8801, then
//   PLAYWRIGHT=<path to playwright/index.mjs> node interactive/tools/play_screenshots.mjs interactive/screenshots
const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const OUT = process.argv[2];
const BASE = "http://127.0.0.1:8801/play/";
const MOVED = "?t=2,0,0,-1&p=srf-2026q2-coj,srf-2026q1-coj&k=35";
const b = await chromium.launch();
const errors = [];
async function page(w, h, query, moved = !!query) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1, colorScheme: "dark", acceptDownloads: true });
  const p = await ctx.newPage();
  p.on("pageerror", e => errors.push(`${w} ${query}: ${e.message}`));
  await p.goto(BASE + query, { waitUntil: "load" });
  await p.waitForFunction(() => /code is ready|effective/.test(document.querySelector('[data-live="engine"] .ess').textContent), null, { timeout: 120000 });
  if (moved) await p.waitForFunction(() => document.querySelector('[data-live="seats"] table tbody tr'), null, { timeout: 120000 });
  await p.waitForTimeout(500);
  return p;
}
for (const [w, h] of [[375, 812], [1440, 1000]]) {
  let p = await page(w, h, "");
  await p.screenshot({ path: `${OUT}/play-${w}-default.png` });
  await p.context().close();
  p = await page(w, h, MOVED);
  await p.screenshot({ path: `${OUT}/play-${w}-moved-top.png` });
  await p.locator("#h-res").scrollIntoViewIfNeeded();
  await p.evaluate(() => window.scrollBy(0, -20));
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/play-${w}-moved-seats.png` });
  await p.click('[data-live="share"] .shareopen');
  await p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.src.startsWith("blob:") && i.complete && i.naturalWidth > 0; }, null, { timeout: 30000 });
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/play-${w}-share.png` });
  if (w === 1440) {
    let d = p.waitForEvent("download"); await p.click('[data-live="share"] .shdl'); await (await d).saveAs(`${OUT}/play-card-1200x630.png`);
  }
  await p.click('[data-live="share"] .sizes button[data-size="story"]');
  await p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.naturalHeight > i.naturalWidth; }, null, { timeout: 30000 });
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/play-${w}-share-story.png` });
  if (w === 1440) {
    let d = p.waitForEvent("download"); await p.click('[data-live="share"] .shdl'); await (await d).saveAs(`${OUT}/play-card-1080x1920.png`);
  }
  await p.context().close();
}
// an invalid link falls back, visibly
const p = await page(1440, 1000, "?t=9,0,0,0&k=7", false);
console.log("invalid-link note:", await p.evaluate(() => document.querySelector('[data-live="engine"] .linknote').textContent));
await p.screenshot({ path: `${OUT}/play-1440-invalid-link.png` });
await b.close();
console.log(errors.length ? errors.join("\n") : "no page errors");
