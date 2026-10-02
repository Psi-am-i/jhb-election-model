// Screenshots of the built /play/ page into interactive/screenshots/play-*.png.
//   build the site, serve site/ on 127.0.0.1:8801, then
//   PLAYWRIGHT=<path to playwright/index.mjs> node interactive/tools/play_screenshots.mjs interactive/screenshots
//
// States (DESIGN §1-2): the untouched page and its card; Black African turnout +5 (first
// screen and whole page, with the map's outlined wards and the ▲▼ against the
// published forecast); a poll believed at half; the share sheet at both sizes
// with a name, and the two images it downloads; an invalid link.
const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const OUT = process.argv[2];
const BASE = "http://127.0.0.1:8801/play/";
const BA5 = "?t=5,0,0,0";
const POLL = "?p=srf-2026q2-coj&k=50";
const b = await chromium.launch();
const errors = [];
async function page(w, h, query, moved = !!query) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1, colorScheme: "dark", acceptDownloads: true });
  const p = await ctx.newPage();
  p.on("pageerror", e => errors.push(`${w} ${query}: ${e.message}`));
  await p.goto(BASE + query, { waitUntil: "load" });
  await p.waitForFunction(() => document.querySelector('[data-live="engine"]').hasAttribute("data-ready"), null, { timeout: 120000 });
  if (moved) await p.waitForFunction(() => document.querySelector('[data-live="seats"] .pl-srow'), null, { timeout: 120000 });
  await p.waitForTimeout(500);
  return p;
}
const cardReady = p => p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.src.startsWith("blob:") && i.complete && i.naturalWidth > 0; }, null, { timeout: 30000 });
for (const [w, h] of [[375, 812], [1440, 1000]]) {
  let p = await page(w, h, "");
  await p.screenshot({ path: `${OUT}/play-${w}-default.png`, fullPage: true });
  if (w === 1440) {
    // the untouched page's card: the model's headline, the name as "Shared by"
    await p.click('[data-live="share"] .pl-shareopen');
    await cardReady(p);
    await p.fill('[data-live="share"] .pl-name', "Thandi");
    await p.waitForFunction(() => /Thandi/.test(document.querySelector('[data-live="share"] .preview img').alt), null, { timeout: 30000 });
    await cardReady(p);
    await p.waitForTimeout(400);
    const d = p.waitForEvent("download"); await p.click('[data-live="share"] .shdl'); await (await d).saveAs(`${OUT}/play-card-untouched-1200x630.png`);
  }
  await p.context().close();
  p = await page(w, h, BA5);
  await p.screenshot({ path: `${OUT}/play-${w}-ba5-fold.png` });
  await p.screenshot({ path: `${OUT}/play-${w}-ba5.png`, fullPage: true });
  await p.click('[data-live="share"] .pl-shareopen');
  await cardReady(p);
  await p.fill('[data-live="share"] .pl-name', "Thandi");
  await p.waitForFunction(() => /Thandi/.test(document.querySelector('[data-live="share"] .preview img').alt), null, { timeout: 30000 });
  await cardReady(p);
  await p.waitForTimeout(400);
  await p.screenshot({ path: `${OUT}/play-${w}-share.png` });
  if (w === 1440) {
    const d = p.waitForEvent("download"); await p.click('[data-live="share"] .shdl'); await (await d).saveAs(`${OUT}/play-card-1200x630.png`);
  }
  await p.click('[data-live="share"] .sizes button[data-size="story"]');
  await p.waitForFunction(() => { const i = document.querySelector('[data-live="share"] .preview img'); return i.naturalHeight > i.naturalWidth; }, null, { timeout: 30000 });
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/play-${w}-share-story.png` });
  if (w === 1440) {
    const d = p.waitForEvent("download"); await p.click('[data-live="share"] .shdl'); await (await d).saveAs(`${OUT}/play-card-1080x1920.png`);
  }
  await p.context().close();
  p = await page(w, h, POLL);
  await p.locator("#h-poll").scrollIntoViewIfNeeded();
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/play-${w}-poll.png` });
  await p.context().close();
}
// an invalid link falls back, visibly
const p = await page(1440, 1000, "?t=9,0,0,0&p=a,b", false);
console.log("invalid-link note:", await p.evaluate(() => document.querySelector('[data-live="engine"] .pl-linknote').textContent));
await p.screenshot({ path: `${OUT}/play-1440-invalid-link.png` });
await b.close();
console.log(errors.length ? errors.join("\n") : "no page errors");
