// Does /your-forecast/ shift while it loads? A headless check (owner,
// 2026-10-10: "the Your Forecast layout must not shift").
//
//   PLAYWRIGHT=<playwright or playwright-core index.mjs> \
//     YF_ROOT=<a built site directory, with site/draws and site/logos linked> \
//     node interactive/tools/yf_shift_check.mjs
//
// yf_jump_check.mjs moves levers on a settled page; it cannot see what moves
// while the page fills. This one opens the page at 375 and 1440 wide, goes
// straight to "Break the model" as its link in the page does, and records the
// browser's own layout-shift entries (PerformanceObserver, type
// "layout-shift": what moved in the window, by how much of it) until section
// 2's seat Worker has answered and the council shows its figures. Two ways
// in: the page opened plainly and scrolled to #break, and the page opened at
// #break.
//
// Two windows, split at the moment section 2's vote list exists (its data,
// forecast.json, has arrived and make.js has built the section):
//   AFTER, until the seat Worker answers: GATED. The council and the
//     coalition chips stand at their size before their figures come (make.js
//     paintPending); a way in passes when its shifts here add up to no more
//     than TOLERANCE.
//   BEFORE: PRINTED, NOT GATED. A reader already at #break before
//     forecast.json arrives sees the vote list and the controls fill in; the
//     map's height is reserved (its viewBox is in the page), the rest is not,
//     because the rows need the roster the data carries. The number is shown
//     with what moved, so it is seen; it has no floor, which would only be
//     lowered when it tripped.
//
// TOLERANCE is the font swap's: the page's fonts arriving over the fallback
// move a line by a pixel or so in its first tenth of a second, which measures
// well under it. Anything that fills in late without its room reserved (the
// vote list, the council, the coalition chips each did) measures far over it.
//
// It proves it looked (CLAUDE.md §4): each way in must reach the Worker's
// answer, and a constructed shift (a block inserted above section 2's
// builder once the page has settled) must be caught, and is, first.
// Exit 0 when every way in passes; 1 with the shifts that failed otherwise.
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const ROOT = process.env.YF_ROOT;
if (!ROOT) throw new Error("set YF_ROOT to a built site directory");
const ORIGIN = "http://yf.local";
const TOLERANCE = 0.01;
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".bin": "application/octet-stream",
  ".py": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2" };

const b = await chromium.launch();
const failures = [];

// The layout-shift entries, each with what moved, from before the page's
// first script runs.
function observe() {
  window.__shifts = [];
  window.__built = null;
  new MutationObserver((_m, mo) => {
    // the section's rows are in: the moment is the end of the frame that
    // first draws them, so the shift that drawing causes falls before it
    if (!document.querySelector(".prlist .prrow:not(.prhead)")) return;
    mo.disconnect();
    requestAnimationFrame(() => requestAnimationFrame(() => { window.__built = performance.now(); }));
  }).observe(document, { childList: true, subtree: true });
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) {
      const what = e.sources.map(s => {
        const n = s.node;
        const d = n && n.nodeType === 1
          ? n.tagName.toLowerCase() + (n.id ? "#" + n.id : "") + (typeof n.className === "string" && n.className.trim() ? "." + n.className.trim().split(/\s+/).join(".") : "")
          : String(n && n.nodeName);
        return `${d} y ${Math.round(s.previousRect.y)}->${Math.round(s.currentRect.y)} h ${Math.round(s.previousRect.height)}->${Math.round(s.currentRect.height)}`;
      });
      window.__shifts.push({ t: Math.round(e.startTime), v: e.value, what });
    }
  }).observe({ type: "layout-shift", buffered: true });
}

async function open(w, hash) {
  const ctx = await b.newContext({ viewport: { width: w, height: 900 }, colorScheme: "dark" });
  await ctx.route(ORIGIN + "/**", route => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname);
    if (p.endsWith("/")) p += "index.html";
    const f = join(ROOT, p);
    if (!existsSync(f) || statSync(f).isDirectory()) return route.fulfill({ status: 404, body: "missing" });
    return route.fulfill({ status: 200, body: readFileSync(f), contentType: TYPES[extname(f)] || "application/octet-stream" });
  });
  await ctx.addInitScript(observe);
  const p = await ctx.newPage();
  p.on("pageerror", e => failures.push(`${w}: page error ${e.message}`));
  await p.goto(ORIGIN + "/your-forecast/" + hash, { waitUntil: "load" });
  return { p, ctx };
}

// Section 2's seat Worker has answered: the council says what it counts.
const answered = p => p.waitForFunction(() => {
  const r = document.querySelector('[data-live="b-council"] .restate');
  return r && r.textContent.trim() && document.querySelector('[data-live="b-council"] .bars .st-row[data-m]');
}, null, { timeout: 240000 });

const total = shifts => shifts.reduce((a, e) => a + e.v, 0);

// it can see: a block inserted above the builder once everything has settled
{
  const { p, ctx } = await open(1440, "#break");
  await answered(p);
  await p.waitForTimeout(800);
  const before = (await p.evaluate(() => window.__shifts)).length;
  await p.evaluate(() => {
    const d = document.createElement("div");
    d.style.height = "200px";
    document.querySelector(".yf-builder").before(d);
  });
  await p.waitForTimeout(500);
  const planted = (await p.evaluate(() => window.__shifts)).slice(before);
  await ctx.close();
  if (total(planted) <= TOLERANCE) {
    console.error(`the check is blind: a constructed shift measured ${total(planted).toFixed(4)}`);
    process.exit(1);
  }
  console.log(`it can see: a constructed shift measured ${total(planted).toFixed(4)} (tolerance ${TOLERANCE})`);
}

for (const w of [375, 1440]) {
  for (const [way, hash, go] of [
    ["opened, then scrolled to #break", "", p => p.evaluate(() => document.querySelector("#break").scrollIntoView())],
    ["opened at #break", "#break", async () => {}],
  ]) {
    const { p, ctx } = await open(w, hash);
    await go(p);
    let reached = true;
    try { await answered(p); } catch (e) { reached = false; }
    await p.waitForTimeout(1500);
    const { shifts, built } = await p.evaluate(() => ({ shifts: window.__shifts, built: window.__built }));
    await ctx.close();
    if (!reached || built === null) {
      failures.push(`${w} ${way}: ${built === null ? "section 2 was never built" : "the seat Worker never answered"}, so the check saw nothing`);
      continue;
    }
    const before = shifts.filter(e => e.t <= built), after = shifts.filter(e => e.t > built);
    const show = list => list.filter(e => e.v > TOLERANCE / 10).map(e => `    ${e.t} ms  ${e.v.toFixed(4)}  ${e.what.join(" | ")}`);
    console.log(`${w} ${way}: after the section is built ${total(after).toFixed(4)} (gated); ` +
                `before it, while forecast.json is on its way, ${total(before).toFixed(4)} (not gated; built at ${Math.round(built)} ms)`);
    for (const line of show(before)) console.log(line);
    if (total(after) > TOLERANCE) failures.push(`${w} ${way}: after the section is built, shifts add up to ${total(after).toFixed(4)}`, ...show(after));
  }
}
await b.close();

if (failures.length) {
  console.error("\nshifts while loading:\n" + failures.join("\n"));
  process.exit(1);
}
console.log("\nno shift once section 2 is built: 2 ways in at 375 and 1440");
