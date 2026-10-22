// Screenshots of the design mock-ups: light at 375 and 1440 px, dark at 1440.
// node audits/2026-10-09-site-batch/design/shoot.mjs   (file:// URLs; no server)
import { chromium } from "/Users/simondavis/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const D = path.dirname(fileURLToPath(import.meta.url));
const pages = ["item1-forecast-callout", "item2-prediction-callout", "item4-cta-a", "item4-cta-b", "item4-cta-c"];
const runs = [["light", 375], ["light", 1440], ["dark", 1440], ["dark", 375]];
const browser = await chromium.launch();
for (const [scheme, width] of runs) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme, deviceScaleFactor: width < 500 ? 2 : 1 });
  const page = await ctx.newPage();
  for (const p of pages) {
    if (scheme === "dark" && width === 375 && !p.startsWith("item4-cta-c")) continue;
    await page.goto(pathToFileURL(path.join(D, p + ".html")).href);
    const ok = await page.evaluate(async () => { await document.fonts.ready;
      return ["16px \"IBM Plex Sans\"", "600 16px \"IBM Plex Serif\"", "600 12px \"IBM Plex Mono\""].map(f => document.fonts.check(f)); });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    const broken = await page.evaluate(() => [...document.images].filter(i => !i.complete || !i.naturalWidth).length);
    const out = `${p}-${width}${scheme === "dark" ? "-dark" : ""}.png`;
    await page.screenshot({ path: path.join(D, out), fullPage: true });
    console.log(out, "fonts", ok.join(","), "overflow", overflow, "brokenImgs", broken);
  }
  await ctx.close();
}
await browser.close();
