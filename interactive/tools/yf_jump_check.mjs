// Does /your-forecast/ jump when a lever moves? A headless check (owner,
// 2026-10-03: "the page must not jump when levers move").
//
//   PLAYWRIGHT=<playwright or playwright-core index.mjs> \
//     YF_ROOT=<a built site directory, e.g. site/> \
//     node interactive/tools/yf_jump_check.mjs
//
// The tool serves YF_ROOT to the browser itself (no port; Pyodide loads from
// cdn.jsdelivr.net). At 375 and 1440 wide it moves every lever of both
// sections, one at a time, and around each move measures the document's
// height, the scroll position, the lever's own place in the viewport, and the
// page position of LANDMARKS, the fixed points below every message region.
// A move passes when none of these changes by more than TOLERANCE_PX.
//
// What a lever move may change: the figures, inside regions of fixed size.
// What it may not: the height of anything a reader reads past. Every message
// that appears or disappears (the status strip, result notes, the stop and
// refusal lines, the toasts) either floats (the computing line, the toast)
// or sits in a region of reserved height (css/your-forecast.css, "Reserved
// message regions").
//
// It proves it looked (CLAUDE.md §4): each move names the message it is
// expected to show, and the check fails if that message never became visible
// with text, so a page that shows nothing cannot pass. A constructed jump
// (a block inserted above the landmarks) must be caught, and is, first.
// Exit 0 when every move passes; 1 with the offending moves otherwise.
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const { chromium } = await import(process.env.PLAYWRIGHT || "playwright");
const ROOT = process.env.YF_ROOT;
if (!ROOT) throw new Error("set YF_ROOT to a built site directory");
const ORIGIN = "http://yf.local";
const TOLERANCE_PX = 1;
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".bin": "application/octet-stream",
  ".py": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2" };

// Fixed points below the message regions, in page order.
const LANDMARKS = ["#h-adjust", ".pl-rgrid", ".pl-mapfig", ".pl-seatfig", ".pl-mapnotes", "#break",
  ".yf-builder", '[data-live="b-vote"]', '[data-live="b-govern"]', ".yf-step4", ".yf-analysis", ".pl-notes"];

const b = await chromium.launch();
const failures = [], looked = [];

async function open(w, h) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: "dark" });
  await ctx.route(ORIGIN + "/**", route => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname);
    if (p.endsWith("/")) p += "index.html";
    const f = join(ROOT, p);
    if (!existsSync(f) || statSync(f).isDirectory()) return route.fulfill({ status: 404, body: "missing" });
    return route.fulfill({ status: 200, body: readFileSync(f), contentType: TYPES[extname(f)] || "application/octet-stream" });
  });
  const p = await ctx.newPage();
  p.on("pageerror", e => failures.push(`${w}: page error ${e.message}`));
  await p.goto(ORIGIN + "/your-forecast/", { waitUntil: "load" });
  await p.waitForFunction(() => document.querySelector('[data-live="engine"]').hasAttribute("data-ready"), null, { timeout: 180000 });
  // section 2 loads its seat engine when it comes into view
  await p.evaluate(() => document.querySelector("#break").scrollIntoView());
  await p.waitForFunction(() => document.querySelector('[data-live="b-council"] .bars .st-row')
    && !document.querySelector('[data-live="b-actions"] .yf-analyse').disabled, null, { timeout: 240000 });
  await settle(p);
  return { p, ctx };
}

// Nothing in flight: the computing line hidden, then two frames and a pause
// for the change cues and any debounced re-analysis.
async function settle(p) {
  await p.waitForTimeout(250);
  await p.waitForFunction(() => document.querySelector('[data-live="busy"]').hidden, null, { timeout: 120000 });
  await p.waitForTimeout(900);
}

function measure(p, lever) {
  return p.evaluate(([lever, marks]) => {
    const y = el => el.getBoundingClientRect().top + window.scrollY;
    const l = document.querySelector(lever);
    // a landmark not rendered (display:none) has no place, so it is left out
    const at = s => { const e = document.querySelector(s); return e && e.getClientRects().length ? y(e) : null; };
    return { height: document.documentElement.scrollHeight, scroll: window.scrollY,
             lever: l ? l.getBoundingClientRect().top : null,
             marks: Object.fromEntries(marks.map(s => [s, at(s)])) };
  }, [lever, LANDMARKS]);
}

// Is `sel` visible with text? Polled while the move settles, so a message
// that shows and then goes (a toast, "Working it out…") still counts.
function watch(p, sel) {
  return p.evaluate(sel => new Promise(resolve => {
    const seen = () => [...document.querySelectorAll(sel)].some(e => e.offsetParent !== null
      && getComputedStyle(e).visibility !== "hidden" && e.textContent.trim() !== "");
    if (seen()) return resolve(true);
    const t0 = performance.now();
    (function tick() { if (seen()) return resolve(true); if (performance.now() - t0 > 20000) return resolve(false); requestAnimationFrame(tick); })();
  }), sel);
}

// YF_JUMP_DEBUG=1: on a jump, every block whose height changed, the deepest first
const DEBUG = !!process.env.YF_JUMP_DEBUG;
function heights(p) {
  return p.evaluate(() => {
    const out = {};
    const path = e => { const a = []; for (let x = e; x && x !== document.body; x = x.parentElement)
      a.unshift(x.tagName.toLowerCase() + (x.id ? "#" + x.id : "") + (x.className && typeof x.className === "string" ? "." + x.className.trim().split(/\s+/).join(".") : "")
        + ":" + [...(x.parentElement?.children || [])].indexOf(x)); return a.join(" > "); };
    for (const e of document.querySelectorAll("#adjust *, #break *, .yf-analysis *")) {
      if (["svg", "path", "g", "line", "text", "pattern", "defs", "b", "i", "span", "a", "sup", "option", "small", "label", "input", "button"].includes(e.tagName.toLowerCase())) continue;
      const r = e.getBoundingClientRect(); if (!r.height && !r.width) continue;
      out[path(e)] = Math.round(r.height);
    }
    return out;
  });
}

function compare(label, before, after, { above = null } = {}) {
  const out = [];
  const d = (a, c) => Math.abs((a ?? 0) - (c ?? 0)) > TOLERANCE_PX;
  if (!above && d(before.height, after.height)) out.push(`document height ${before.height} -> ${after.height}`);
  if (d(before.scroll, after.scroll)) out.push(`scroll ${before.scroll} -> ${after.scroll}`);
  if (d(before.lever, after.lever)) out.push(`lever ${before.lever} -> ${after.lever} in the viewport`);
  for (const [s, v] of Object.entries(before.marks)) {
    if (v == null || after.marks[s] == null) continue;
    if (above && v > before.marks[above]) continue;
    if (d(v, after.marks[s])) out.push(`${s} ${v} -> ${after.marks[s]}`);
  }
  return out.length ? `${label}: ${out.join("; ")}` : null;
}

// One move: scroll the lever to the middle of the screen, measure, act, watch
// for the message the move should show, settle, measure again.
async function move(p, w, label, lever, act, shows, { scrolls = false, above = null } = {}) {
  await p.evaluate(s => document.querySelector(s).scrollIntoView({ block: "center" }), lever);
  await p.waitForTimeout(300);
  const before = await measure(p, lever);
  const hb = DEBUG ? await heights(p) : null;
  const seen = shows ? watch(p, shows) : Promise.resolve(true);
  await act();
  const saw = await seen;
  await settle(p);
  const after = await measure(p, lever);
  if (shows) { looked.push(`${w} ${label}: ${shows} ${saw ? "seen" : "NOT SEEN"}`); if (!saw) failures.push(`${w} ${label}: ${shows} never showed`); }
  // a move that scrolls the page by design (the first "Analyse") is made
  // for the state it leaves, not measured
  const jump = scrolls ? null : compare(`${w} ${label}`, before, after, { above });
  if (jump) failures.push(jump);
  if (jump && DEBUG) {
    const ha = await heights(p);
    const changed = Object.keys(hb).filter(k => k in ha && Math.abs(hb[k] - ha[k]) > 1)
      .filter((k, _i, all) => !all.some(o => o !== k && o.startsWith(k + " > ")));
    for (const k of changed) failures.push(`    ${hb[k]} -> ${ha[k]}  ${k.split(" > ").slice(-3).join(" > ")}`);
  }
  return jump;
}

const slide = (sel, v) => p => p.evaluate(([s, v]) => { const i = document.querySelector(s); i.value = String(v);
  i.dispatchEvent(new Event("input", { bubbles: true })); }, [sel, v]);
const pick = sel => p => p.evaluate(s => { const i = document.querySelector(s); i.checked = true;
  i.dispatchEvent(new Event("change", { bubbles: true })); }, sel);
const click = sel => p => p.evaluate(s => document.querySelector(s).click(), sel);

for (const [w, h] of [[375, 812], [1440, 1000]]) {
  const { p, ctx } = await open(w, h);
  // the detector sees: a block inserted above every landmark is a jump
  {
    const before = await measure(p, "#h-adjust");
    await p.evaluate(() => { const x = document.createElement("div"); x.id = "jump-probe"; x.style.height = "40px";
      document.querySelector("#adjust").prepend(x); });
    const caught = compare("probe", before, await measure(p, "#h-adjust"));
    await p.evaluate(() => document.querySelector("#jump-probe").remove());
    const quiet = compare("probe", before, await measure(p, "#h-adjust"));
    if (!caught || quiet) failures.push(`${w}: the detector is blind (caught ${!!caught}, quiet after revert ${!quiet})`);
  }
  const T0 = "#t-0", T1 = "#t-1", VOTE = ".prlist .prrow input.prnum";
  // the first party of "Other parties", seated nowhere at the start
  const NEW = '[data-live="b-vote"] .prmore .prrow input.prnum';
  const voteAt = (sel, v) => async p => { const i = p.locator(sel).first(); await i.fill(String(v)); await i.press("Enter"); };
  const vote = v => voteAt(VOTE, v);
  // Section 2 follows section 1 until the reader edits it (make.js), so
  // while it is unedited a section-1 lever redraws its council: rows and
  // chips, which are content. That pass is held to everything down to
  // section 2's council; the full pass below, with section 2 edited, to the
  // whole document.
  const FOLLOWS = ".yf-builder";
  const S = [
    ["turnout +5, section 2 following", T0, slide(T0, 5), '[data-live="result"] .pl-status', { above: FOLLOWS }],
    ["by-elections, section 2 following", '[data-live="cells"]', click('[data-live="cells"] button:first-child'), null, { above: FOLLOWS }],
    ["back to the forecast, section 2 following", '[data-live="result"]', click('[data-live="result"] .pl-back'), null, { above: FOLLOWS }],
    // section 2 edited: from here it holds its own forecast
    ["paint a ward", ".wardmap", async p => {
      // a DOM click: the reader's click does not scroll, Playwright's would
      // bring the last of the chips into view first
      await p.evaluate(() => [...document.querySelectorAll(".brushscroll button")].pop().click());
      await p.locator(".wardmap [data-i]").nth(7).click({ force: true });
    }, ".nchanged"],
    ["turnout +5", T0, slide(T0, 5), '[data-live="b-status"] .yf-follow'],
    // two groups far apart: the simulations run out and the slider stops
    // the stop is said under the turnout sliders, with the zone shaded (B1)
    ["a second group to -5 (stops)", T1, slide(T1, -5), '[data-live="turnout"] .pl-zonewhy'],
    // the stop is in the DOM, not only in the source (diff review, 2026-10-05):
    // the line has words and the track past the stop is shaded
    p => p.evaluate(() => [document.querySelector('[data-live="turnout"] .pl-zonewhy').textContent.trim(),
      document.querySelectorAll('[data-live="turnout"] svg.pl-zone rect').length])
      .then(([why, rects]) => {
        looked.push(`stop: "${why.slice(0, 70)}", ${rects} shaded zone(s)`);
        if (!why || !rects) failures.push(`the stop shows ${why ? "" : "no reason "}${rects ? "" : "no shaded zone"}`);
      }),
    ["the second group back to 0", T1, slide(T1, 0), null],
    ["turnout back to 0", T0, slide(T0, 0), null],
    ["a poll", '[data-live="polls"]', pick('[data-live="polls"] input[type="radio"]:not([value=""])'), null],
    ["trust up", "#trust", slide("#trust", 50), null],
    ["no poll", '[data-live="polls"]', pick('[data-live="polls"] input[value=""]'), null],
    ["by-elections", '[data-live="cells"]', click('[data-live="cells"] button:first-child'), '[data-live="byelection"] .pl-note'],
    ["seat law", '[data-live="law"]', pick('[data-live="law"] input:not([value="deduct"])'), ".pl-sharewhy"],
    ["seat law back", '[data-live="law"]', pick('[data-live="law"] input[value="deduct"]'), null],
    ["back to the forecast", '[data-live="result"]', click('[data-live="result"] .pl-back'), null],
    // section 2
    ["paint another ward", ".wardmap", p => p.locator(".wardmap [data-i]").nth(20).click({ force: true }), null],
    ["a party's vote", VOTE, vote(30), null],
    // a party taken to zero keeps its row; a typed vote over 100 is capped
    // at the most the party can have, which takes most parties to zero
    // (review of the share build, 2026-10-03: both moved the vote box at 375)
    ["a party's vote to 0", VOTE, vote(0), null],
    ["a party's vote typed over 100", VOTE, vote(150), '[data-live="b-vote"] .floornote'],
    ["a party's vote back", VOTE, vote(30), null],
    // a party seated nowhere at the start gets its first seats: its row
    // fills the council's reserved room (JUDGEMENT-CALLS §N5); its new
    // coalition chip is below the lever, so that pass is held down to the
    // coalition's region
    p => p.evaluate(() => { document.querySelector('[data-live="b-vote"] .prmore').open = true; }),
    ["a new party's first seats", NEW, voteAt(NEW, 3), null, { above: '[data-live="b-govern"]' }],
    // "Next" after the vote: the focus lands on the first coalition chip (B5)
    p => p.locator('[data-live="b-vote"] .yf-next').click().then(() => p.waitForTimeout(800))
      .then(() => p.evaluate(() => !!document.activeElement && document.activeElement.matches('[data-live="b-govern"] .coal > *')))
      .then(ok => { looked.push(`next after the vote: focus on the first coalition chip ${ok ? "yes" : "NO"}`);
        if (!ok) failures.push("Next after the vote leaves the focus off the coalition's first chip"); }),
    ["a coalition party", ".coal", p => p.locator(".coal button").first().click(), ".coalstat"],
    ["analyse", ".yf-step4", p => p.locator('[data-live="b-actions"] .yf-analyse').click(), '[data-live="b-analysis"] .yf-abadge', { scrolls: true }],
    ["edit after analysing", VOTE, vote(25), null],
    ["a second coalition party after analysing", ".coal", p => p.locator(".coal button").nth(1).click(), null],
  ];
  for (const m of S) {
    if (typeof m === "function") { await m(p); await settle(p); continue; }   // a step that is not a lever move
    const [label, lever, act, shows, opt] = m;
    await move(p, w, label, lever, () => act(p), shows, opt);
  }
  // every lever at once, the longest every message gets: no slot overflows
  for (const [sel, v] of [["#t-0", 5], ["#t-1", 5], ["#t-2", 5], ["#t-3", 5]]) { await slide(sel, v)(p); await settle(p); }
  await pick('[data-live="polls"] input[type="radio"]:not([value=""])')(p); await settle(p);
  await slide("#trust", 100)(p); await settle(p);
  await click('[data-live="cells"] button:first-child')(p); await settle(p);
  await pick('[data-live="law"] input:not([value="deduct"])')(p); await settle(p);
  const over = await p.evaluate(() => [...document.querySelectorAll(".yf-slot")].filter(e => e.getClientRects().length)
    .map(e => [e.className, e.scrollHeight - e.clientHeight, e.textContent.trim().slice(0, 60)]).filter(([, d]) => d > 1));
  for (const [c, d, t] of over) failures.push(`${w} every lever: .${c.replace(/ /g, ".")} overflows by ${d}px ("${t}")`);
  // wide: no VISIBLE inner scroll bar anywhere on the page (owner,
  // 2026-10-05). An element may scroll on its own with its bar hidden, as the
  // levers' column does so the results stay beside the lever being moved
  // (owner, 2026-10-05); it fails when it scrolls up and down with more than
  // it shows AND shows a bar: a computed scrollbar-width other than "none",
  // and a bar that takes width (offsetWidth - clientWidth, less the borders).
  // Playwright's headless Chromium runs with --hide-scrollbars, where no bar
  // takes width: the constructed visible scroller measures its own bar, and
  // where that reads zero the width term is dropped and scrollbar-width alone
  // decides, which the check says. (A phone's chip tray and map scroll
  // sideways by design.)
  const scrolling = byWidth => p.evaluate(byWidth => [...document.querySelectorAll("body *")].filter(e => e.getClientRects().length)
    .filter(e => { const s = getComputedStyle(e);
      const bar = e.offsetWidth - e.clientWidth - parseFloat(s.borderLeftWidth) - parseFloat(s.borderRightWidth);
      return ["auto", "scroll"].includes(s.overflowY) && e.scrollHeight - e.clientHeight > 1
        && s.scrollbarWidth !== "none" && (!byWidth || bar > 0); })
    .map(e => `${e.tagName.toLowerCase()}${e.id ? "#" + e.id : ""}.${String(e.className).trim().replace(/\s+/g, ".")} by ${e.scrollHeight - e.clientHeight}px`), byWidth);
  let byWidth = false;
  if (w >= 980) {   // the detector catches a constructed visible scroller, passes a hidden one, and goes quiet when they are removed
    byWidth = await p.evaluate(() => {
      const probe = (id, css) => { const x = document.createElement("div"); x.id = id; x.style.cssText = "height:10px;overflow-y:auto;" + css;
        x.append(Object.assign(document.createElement("div"), { style: "height:40px" })); document.querySelector("#adjust").append(x); return x; };
      const shown = probe("scroll-probe", "");
      probe("scroll-probe-hidden", "scrollbar-width:none");
      return shown.offsetWidth - shown.clientWidth > 0;
    });
    looked.push(`${w}: scroll bars ${byWidth ? "take width here, so a bar fails when it is not set to none and takes width"
      : "take no width in this browser (--hide-scrollbars), so scrollbar-width alone decides"}`);
    const found = await scrolling(byWidth);
    const seen = found.some(x => x.startsWith("div#scroll-probe."));
    const passed = !found.some(x => x.startsWith("div#scroll-probe-hidden."));
    await p.evaluate(() => { document.querySelector("#scroll-probe").remove(); document.querySelector("#scroll-probe-hidden").remove(); });
    const quiet = !(await scrolling(byWidth)).some(x => x.startsWith("div#scroll-probe"));
    if (!seen || !passed || !quiet)
      failures.push(`${w}: the scroll-bar check is blind (caught the visible probe ${seen}, passed the hidden one ${passed}, quiet after removal ${quiet})`);
  }
  const scrollers = w < 980 ? [] : await scrolling(byWidth);
  if (w >= 980) looked.push(`${w} every lever: ${scrollers.length} inner scroller(s) with a visible bar`);
  for (const x of scrollers) failures.push(`${w} every lever: ${x} scrolls inside the page with a visible scroll bar`);
  // the settings line: clamped to its strip, the rest behind "+N more"
  looked.push(`${w} every lever: the settings line shows "${await p.evaluate(() => document.querySelector(".pl-settings").textContent)}"`);
  await ctx.close();
}
await b.close();
console.log(looked.join("\n"));
if (failures.length) { console.log("\nJUMPS:\n" + failures.join("\n")); process.exit(1); }
console.log(`\nno jump: ${looked.length} watched messages, every lever at 375 and 1440`);
