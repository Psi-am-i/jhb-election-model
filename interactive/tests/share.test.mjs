// Sharing a reader's forecast (audits/2026-10-03-share-design): the cards
// (js/share-card.js), their fonts, the edge's card for a link
// (src/share-edge.js's cardFor, with a fake seat Worker) and the seal
// (src/seal.js).
//
//   node --test interactive/tests/share.test.mjs
//
// The two forecasts are interactive/tests/share-fixture.json, written by
// interactive/tools/share_fixture.py from the project's own code; the page's
// data is src/build_make.py's forecast_data(), computed here.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import * as SC from "../js/share-card.js";
import * as B from "../js/builder-state.js";
import * as MS from "../js/make-state.js";
import { NAME_MAX } from "../js/play-state.js";
import { render as renderFonts, OUT as FONTS_OUT, FACES as FONT_FILES } from "../tools/card_fonts.mjs";
import { FIXTURE, assets, specs, toPNG, MADE } from "../tools/render_cards.mjs";
import { makeSeal, checkSeal } from "../../src/seal.js";
import * as EDGE from "../../src/share-edge.js";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../..");
const { party, A, B: Bspec } = specs();
const ASSETS = assets();

// ---------- fonts ----------

test("the width table is the card fonts' own, and the edge bundles exactly those files", () => {
  assert.equal(readFileSync(FONTS_OUT, "utf8"), renderFonts(), "run node interactive/tools/card_fonts.mjs");
  const render = readFileSync(resolve(repo, "src/og-render.js"), "utf8");
  const imported = [...render.matchAll(/from "\.\/card-fonts\/([^"]+\.ttf)"/g)].map(m => m[1]).sort();
  assert.deepEqual(imported, Object.values(FONT_FILES).map(f => f[0]).sort());
  assert.ok(imported.length >= 4);
});

test("a measured string is as wide as resvg draws it: never wider by over 2 px, narrower only by kerning", async () => {
  const { Resvg } = await import("../../worker-api/node_modules/@resvg/resvg-wasm/index.mjs");
  await toPNG("<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'/>");   // initialises the wasm
  const fonts = Object.values(FONT_FILES).map(([f]) => readFileSync(resolve(repo, "src/card-fonts", f)));
  const { FACES } = await import("../js/card-fonts.js");
  // the right edge of a bar drawn after the text, less the same bar's right
  // edge with no text before it: the text's drawn advance
  const right = (face, s, fs) => {
    const f = FACES[face];
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="200"><text x="10" y="100" font-family="${f.family}" font-weight="${f.weight}" font-size="${fs}">${s.replace(/&/g, "&amp;").replace(/</g, "&lt;")}|</text></svg>`;
    const r = new Resvg(svg, { font: { fontBuffers: fonts.map(b => new Uint8Array(b)), loadSystemFonts: false } });
    const box = r.getBBox();
    r.free();
    return box.x + box.width;
  };
  for (const [face, s, fs] of [["serifSemi", "Thandi's Election Forecast", 56], ["sans", "Governing: ANC and DA, 137 seats.", 22],
    ["monoSemi", SC.SITE, 19], ["sansBold", "100", 26], ["sansSemi", "MK Party", 23]]) {
    const drawn = right(face, s, fs) - right(face, "", fs), measured = SC.textWidth(s, fs, face);
    // never wider than measured by more than 2 px; narrower only by resvg's
    // kerning, which the advance table leaves out (a headline errs short)
    assert.ok(drawn <= measured + 2, `${face} "${s}": drawn ${drawn}, measured ${measured}`);
    assert.ok(measured - drawn <= 2 + measured * 0.005, `${face} "${s}": drawn ${drawn}, measured ${measured}`);
  }
});

// ---------- the council graphic ----------

function councilSpec(council, majority, first = 140) {
  const rows = [{ code: "P", name: "P", colour: "#111111", seats: first, ward: 70, pr: first - 70 },
    { code: "Q", name: "Q", colour: "#222222", seats: council - first, ward: 65, pr: council - first - 65 }];
  return { rows, council, majority, coalition: [] };
}

test("the majority step encloses exactly majority - 1 seats, whatever the council's size", () => {
  for (const council of [269, 270, 272]) {
    const majority = Math.floor(council / 2) + 1;
    const L = SC.councilLayout(councilSpec(council, majority));
    assert.equal(L.cells.length, council);
    // the cells left of or above the step: whole columns before it, and the
    // rows above it in its own column
    const inside = L.cells.filter(c => c.col < L.step.col || (c.col === L.step.col && c.row < L.step.row));
    assert.equal(inside.length, majority - 1, `council ${council}`);
    assert.equal(L.cols, Math.ceil(council / 10));
    // and the path is drawn where the layout says
    const d = SC.stepPath(L, 10, 2);
    assert.ok(d.startsWith("M") && (L.step.row === 0 ? !d.includes("H") : d.includes("H")));
  }
  // it can see: a majority one higher moves the step by one seat
  const L1 = SC.councilLayout(councilSpec(270, 136)), L2 = SC.councilLayout(councilSpec(270, 137));
  assert.equal(L2.step.col * 10 + L2.step.row - (L1.step.col * 10 + L1.step.row), 1);
});

test("governing parties fill first, in seat order, ward seats before PR seats", () => {
  const L = SC.councilLayout(A);
  const order = [...new Set(L.cells.map(c => c.code))];
  assert.deepEqual(order.slice(0, A.coalition.length), A.coalition);
  for (const r of A.rows) {
    const mine = L.cells.filter(c => c.code === r.code);
    assert.equal(mine.length, r.seats);
    assert.ok(mine.every((c, i) => c.pr === (i >= r.ward)), r.code);
  }
});

// ---------- words and neutrality ----------

test("the headline is Title Case and the name is drawn as text, escaped", () => {
  assert.equal(SC.cardTitle("Thandi"), "Thandi's Election Forecast");
  assert.equal(SC.cardTitle("James"), "James' Election Forecast");
  assert.equal(SC.cardTitle(""), "My Election Forecast");
  const spec = { ...A, name: "<A & B>", title: SC.cardTitle("<A & B>") };
  const svg = SC.linkCardSVG(spec, ASSETS, party);
  assert.ok(svg.includes("&lt;A &amp; B&gt;'s Election Forecast"));
  assert.ok(!svg.includes("<A & B>"));
});

test("a name of NAME_MAX characters fits the link card at 40 px or more, or is cut with an ellipsis", () => {
  for (const name of ["W".repeat(NAME_MAX), "Wm".repeat(NAME_MAX / 2), "i".repeat(NAME_MAX)]) {
    const t = SC.cardTitle(name);
    const svg = SC.linkCardSVG({ ...A, name, title: t }, ASSETS, party);
    const m = new RegExp(`<text x="48" y="${SC.LINK_HEAD_Y}"[^>]*font-size="([\\d.]+)"[^>]*>([^<]*)<\\/text>`).exec(svg);
    assert.ok(m, "the headline is drawn");
    const fs = Number(m[1]);
    assert.ok(fs >= 40, name);
    const shown = m[2].replace(/&#x27;|&apos;/g, "'");
    assert.ok(shown === t || shown.endsWith("\u2026"), shown);
    assert.ok(SC.textWidth(shown, fs, "serifSemi") <= 900 + 0.5);
  }
});

test("the outcome reads exactly as the chance is defined, and a tie splits the band and colours each tied row", () => {
  const the = c => party(c).article + party(c).name;
  assert.equal(A.words, SC.outcomeWords(A.outcome, party));
  assert.ok(A.words.startsWith(the(A.outcome.largest).replace(/^t/, "T") + " is the largest party, no party has a majority"));
  // a constructed tie: two parties on the most seats
  const [p, q] = A.rows;
  const answer = { ...FIXTURE.A.answer, seats: { ...FIXTURE.A.answer.seats, [q.code]: p.seats } };
  const tie = SC.forecastSpec({ name: "T", answer, outcome: { ...A.outcome, largest: null }, vote: FIXTURE.A.vote,
    calls: A.calls, party, baseline: FIXTURE.baseline, election: FIXTURE.election });
  assert.deepEqual(tie.top.sort(), [p.code, q.code].sort());
  assert.ok(!/largest/.test(tie.words) && /tie for the most seats/.test(tie.words));
  const svg = SC.linkCardSVG(tie, ASSETS, party);
  const headBand = new RegExp(`<rect x="([\\d.]+)" y="0" width="([\\d.]+)" height="${SC.LINK_BAND}" fill="([^"]+)"`, "g");
  const band = [...svg.matchAll(headBand)];
  assert.equal(band.length, 2);
  assert.deepEqual(band.map(b => b[3]).sort(), [p.colour, q.colour].sort());
  assert.ok(Math.abs(band.reduce((a, b) => a + Number(b[2]), 0) - SC.SIZES.link[0]) <= 1, "the halves span the card");
  // the table: each tied party's row in its colour, no other row
  const rowBands = svg => [...svg.matchAll(/<rect x="[\d.]+" y="[\d.]+" width="[\d.]+" height="34" fill="([^"]+)"/g)].map(m => m[1]);
  assert.deepEqual(rowBands(svg).sort(), [p.colour, q.colour].sort());
  // one largest party: one band, its colour, and its row alone in colour
  const one = SC.linkCardSVG(A, ASSETS, party);
  assert.deepEqual([...one.matchAll(headBand)].map(b => b[3]), [A.rows[0].colour]);
  assert.deepEqual(rowBands(one), [A.rows[0].colour]);
  assert.ok(!rowBands(one).includes(SC.OTHERS_COLOUR), "Others is never coloured");
});

test("the two-forecast card's band follows each forecast's largest party, half each", () => {
  const svg = SC.duelCardSVG(A, Bspec, ASSETS, party);
  const band = [...svg.matchAll(new RegExp(`<rect x="([\\d.]+)" y="0" width="([\\d.]+)" height="${SC.DUEL_BAND}" fill="([^"]+)"`, "g"))];
  const half = SC.SIZES.duel[0] / 2;
  const colours = side => band.filter(b => (Number(b[1]) < half) === side).map(b => b[3]);
  const tops = F => F.top.map(c => F.rows.find(r => r.code === c).colour);
  assert.deepEqual(colours(true), tops(A));
  assert.deepEqual(colours(false), tops(Bspec));
});

test("text on a band is the ink that reads on it", () => {
  const light = SC.inkOn(["#ffffff"]), dark = SC.inkOn(["#000000"]);
  assert.notEqual(light, dark);
  // a split band takes the ink with the better worst case: on white and
  // black together, whichever, but the same for either order
  assert.equal(SC.inkOn(["#ffffff", "#000000"]), SC.inkOn(["#000000", "#ffffff"]));
  for (const r of A.rows) assert.ok([light, dark].includes(SC.inkOn([r.colour])), r.code);
});

test("% of seats is the seats over the council, for every row and Others, on both single cards", () => {
  for (const F of [A, Bspec]) {
    const rows = SC.listedRows(F, SC.ROWS.link);
    for (const r of rows) assert.equal(r.seatPct, SC.seatShare(r.seats, F.council), r.name);
    for (const r of rows) assert.ok(Math.abs(r.seatPct - r.seats / F.council * 100) < 1e-9, r.name);
    assert.ok(Math.abs(rows.reduce((a, r) => a + r.seatPct, 0) - 100) < 1e-9, "the shares sum to the council");
    for (const [card, n] of [[SC.linkCardSVG(F, ASSETS, party), SC.ROWS.link], [SC.storyCardSVG(F, ASSETS, party), SC.ROWS.story]]) {
      for (const r of SC.listedRows(F, n)) {
        assert.ok(card.includes(">" + r.seatPct.toFixed(1) + "%<"), r.name + " % of seats");
        assert.ok(card.includes(">" + r.vote.toFixed(1) + "%<"), r.name + " % of votes");
      }
      for (const w of [">% of<", ">seats<", ">votes<", ">Change<", ">vs " + F.baseYear + "<"]) assert.ok(card.includes(w), w);
    }
  }
});

test("the card modules name no party, hold no party's colour, and compute no badge", () => {
  const files = ["js/share-card.js", "js/make-share.js", "js/arrival.js"].map(f => [f, readFileSync(resolve(here, "..", f), "utf8")]);
  const looked = [];
  for (const [code, p] of Object.entries(FIXTURE.parties)) {
    if (code.length < 2) continue;
    looked.push(code);
    for (const [f, text] of files) {
      assert.ok(!new RegExp(`["'\\b]${code}["'\\b]`).test(text), `${f} names ${code}`);
      if (p.colour !== "#8b918b") assert.ok(!text.toLowerCase().includes(p.colour.toLowerCase()), `${f} holds ${code}'s colour`);
      if (p.name.length > 3) assert.ok(!text.includes('"' + p.name + '"'), `${f} names ${p.name}`);
    }
  }
  assert.ok(looked.length > 20, "the scan looked at the roster");
  for (const [f, text] of files) for (const w of ["Safe call", "Bold call", "Wild call"]) assert.ok(!text.includes(w), `${f} types ${w}`);
  // it can see: a module that typed a party's code is caught
  const code = Object.keys(FIXTURE.parties).find(c => c.length > 2);
  assert.ok(new RegExp(`["'\\b]${code}["'\\b]`).test(`x = "${code}";`));
});

test("rows past the card's count are summed as Others, and a tie at the cut is never split", () => {
  const rows = SC.listedRows(A, SC.ROWS.link);
  assert.equal(rows.at(-1).name, "Others");
  assert.equal(rows.reduce((a, r) => a + r.seats, 0), A.council);
  const seats = { a: 10, b: 9, c: 3, d: 3, e: 3, f: 1 };
  assert.deepEqual(SC.cutAt(Object.keys(seats), seats, 3), ["a", "b"]);
  assert.deepEqual(SC.cutAt(Object.keys(seats), seats, 4), ["a", "b", "c", "d", "e"]);
});

test("vs the previous election: 'new' for a party not on that ballot, a signed difference otherwise", () => {
  for (const r of A.rows) {
    if (r.code in FIXTURE.baseline.vote) {
      assert.equal(r.seatsVs, SC.signed(r.seats - (FIXTURE.baseline.seats[r.code] || 0)));
      assert.match(r.voteVs, /^[+\u2212\u00b1]\d+\.\d$/);
    } else {
      assert.equal(r.seatsVs, "new");
      assert.equal(r.voteVs, "new");
    }
  }
  assert.ok(A.rows.some(r => r.seatsVs === "new") && A.rows.some(r => r.seatsVs !== "new"));
});

test("the sealing time and the days to the vote are the election's own clock", () => {
  const e = FIXTURE.election;
  assert.equal(SC.localStamp(Date.parse("2026-10-03T22:30:00Z"), e), "4 October 2026, 00:30 " + e.zone);
  assert.equal(SC.daysToVote(Date.parse(e.polls_open), e), 0);
  assert.equal(SC.daysToVote(Date.parse(e.polls_open) - 864e5, e), 1);
  assert.equal(SC.madeText({ ...A, made: null }), "");
  assert.match(SC.madeText(A), /^Sealed \d+ \w+ \d{4}, \d\d:\d\d /);
  assert.match(SC.madeText({ ...A, made: { at: MADE.at, sealed: false } }), /^Made \d+ \w+ \d{4}$/);
});

// ---------- the images ----------

const pngSize = buf => [buf.readUInt32BE(16), buf.readUInt32BE(20)];

test("each card rasterises at its size with the edge's renderer", async () => {
  for (const [size, svg] of [["link", SC.linkCardSVG(A, ASSETS, party)], ["story", SC.storyCardSVG(A, ASSETS, party)],
    ["duel", SC.duelCardSVG(A, Bspec, ASSETS, party)]]) {
    const png = Buffer.from(await toPNG(svg));
    assert.equal(png.subarray(1, 4).toString(), "PNG");
    assert.deepEqual(pngSize(png), SC.SIZES[size], size);
  }
});

test("the story card keeps its words above the band story apps cover", () => {
  for (const F of [A, Bspec, { ...Bspec, excess: [A.excess[0] || "x", "A second long note about wards and seats that wraps."] }]) {
    const svg = SC.storyCardSVG(F, ASSETS, party);
    const ys = [...svg.matchAll(/<text x="[\d.]+" y="([\d.]+)"/g)].map(m => Number(m[1]));
    assert.ok(Math.max(...ys) <= SC.STORY_TEXT_BOTTOM, String(Math.max(...ys)));
  }
});

// ---------- the edge's card for a link ----------

const PY = resolve(repo, ".venv/bin/python");
const D = JSON.parse(execFileSync(PY, ["-c",
  "import json, sys; sys.path.insert(0, 'src'); import build_make; print(json.dumps(build_make.forecast_data()))"],
  { cwd: repo, maxBuffer: 1 << 28 }));
const ctx = B.contextOf(D.schema);
const stateA = B.startState(ctx, { calls: FIXTURE.A.calls, share: FIXTURE.A.vote }, FIXTURE.A.calls).state;
const fA = MS.encode(stateA, FIXTURE.A.coalition, ctx);
const KEY = "test-only-seal-key";

function fakeEnv({ seats = true, key = KEY } = {}) {
  const files = { "/your-forecast/forecast.json": JSON.stringify(D),
    "/your-forecast/parties.json": JSON.stringify(FIXTURE.parties),
    "/logo.svg": readFileSync(resolve(repo, "site/logo.svg"), "utf8") };
  const logos = new Set(readdirSync(resolve(repo, "site/logos")));
  const asked = [];
  return { asked, env: {
    ...(key ? { SEAL_KEY: key } : {}),
    ASSETS: { async fetch(req) {
      const p = new URL(req.url).pathname;
      if (files[p]) return new Response(files[p], { status: 200 });
      const m = /^\/logos\/(.+)$/.exec(p);
      if (m && logos.has(m[1])) return new Response(readFileSync(resolve(repo, "site/logos", m[1])), { status: 200 });
      return new Response("missing", { status: 404 });
    } },
    ...(seats ? { SEATS: { async fetch(u, init) {
      const body = JSON.parse(init.body);
      asked.push(body);
      // the fixture's answer for its own picks, as the seat Worker would give it
      return new Response(JSON.stringify({ ...FIXTURE.A.answer, code_ref: "ab".repeat(32), draws_sha256: body.draws_sha256 }), { status: 200 });
    } } } : {}),
  } };
}

test("the edge draws the link's own forecast from the seat Worker's answer, sealed or not", async () => {
  EDGE.forgetPageData();
  const fields = { v: "1", c: D.context_ref, f: fA, n: "Thandi" };
  const at = Date.parse("2026-10-03T10:05:00Z");
  const s = await makeSeal(KEY, fields, at);
  const q = new URLSearchParams({ ...fields, s }).toString();
  const { env, asked } = fakeEnv();
  const card = await EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q), env, "link");
  const svg = card.svg;
  assert.equal(card.sealed, true);
  assert.match(EDGE.imageCache(card.sealed), /immutable/);
  assert.ok(svg.includes("Thandi's Election Forecast"));
  assert.ok(svg.includes(SC.chanceSentence(FIXTURE.A.answer.outcome.text).replace(/'/g, "'")));
  assert.ok(svg.includes(">" + FIXTURE.A.answer.outcome.badge + "<"));
  assert.ok(svg.includes("Sealed " + SC.localStamp(at, D.election)));
  assert.equal(asked.length, 1);
  assert.deepEqual(asked[0].coalition, FIXTURE.A.coalition);
  assert.equal(asked[0].draws_sha256, D.draws_sha256);
  // relabelled: the seal no longer holds, and the card says nothing about when
  const q2 = new URLSearchParams({ ...fields, n: "Someone", s }).toString();
  const card2 = await EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q2), fakeEnv().env, "link");
  const svg2 = card2.svg;
  assert.equal(card2.sealed, false);
  assert.equal(EDGE.imageCache(card2.sealed), "public, max-age=" + EDGE.UNSEALED_MAX_AGE_S);
  assert.ok(!svg2.includes("Sealed") && !svg2.includes("Made "));
  // no key: the same sealed link draws unsealed
  assert.equal((await EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q), fakeEnv({ key: null }).env, "link")).sealed, false);
  // a return link draws both forecasts
  const q3 = new URLSearchParams({ ...fields, vs: fA, vn: "Kgomotso" }).toString();
  const svg3 = (await EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q3), fakeEnv().env, "link")).svg;
  assert.ok(svg3.includes(">Thandi<") && svg3.includes(">Kgomotso<") && svg3.includes("Difference"));
  // no seat Worker: no card
  await assert.rejects(EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q), fakeEnv({ seats: false }).env, "link"));
});

test("an answer that breaks the seat law's arithmetic draws no card", async () => {
  EDGE.forgetPageData();
  const { env } = fakeEnv();
  const bad = { ...env, SEATS: { async fetch() {
    const a = FIXTURE.A.answer;
    const k = Object.keys(a.seats)[0];
    return new Response(JSON.stringify({ ...a, seats: { ...a.seats, [k]: a.seats[k] + 5 }, code_ref: "ab".repeat(32), draws_sha256: D.draws_sha256 }), { status: 200 });
  } } };
  const q = new URLSearchParams({ v: "1", c: D.context_ref, f: fA }).toString();
  await assert.rejects(EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q), bad, "link"));
});

// ---------- the seal ----------

test("a seal made under an earlier context still checks; the answer says the page cannot read it", async () => {
  EDGE.forgetPageData();
  const fields = { v: "1", c: "an-earlier-context", f: fA, n: "Thandi" };
  const at = Date.parse("2026-10-03T10:05:00Z");
  const s = await makeSeal(KEY, fields, at);
  const ask = body => EDGE.sealCheck(new Request("https://joburg.whysoserious.city/seal/1/check", { method: "POST", body: JSON.stringify(body) }),
                                     fakeEnv().env, new URL("https://joburg.whysoserious.city/seal/1/check"));
  const old = await (await ask({ ...fields, s })).json();
  assert.deepEqual(old, { sealed: true, at: new Date(Math.floor(at / 1000) * 1000).toISOString(), before_polls: true, readable: false });
  const forged = await (await ask({ ...fields, n: "Someone", s })).json();
  assert.deepEqual(forged, { sealed: false, at: null, before_polls: false, readable: false });
  // and sealing is refused for a forecast the page cannot read, and on a preview
  const sealAt = (body, opt) => EDGE.seal(new Request("https://x/seal/1", { method: "POST", body: JSON.stringify(body) }),
                                          fakeEnv().env, new URL("https://joburg.whysoserious.city/seal/1"), opt);
  assert.equal((await sealAt(fields)).status, 400);
  assert.equal((await sealAt({ ...fields, c: D.context_ref }, { preview: true })).status, 403);
});

test("a seal holds for exactly the state and name it signed, under its key", async () => {
  const fields = { v: "1", c: "abc", f: "AQID", n: "Thandi" };
  const at = Date.parse("2026-10-03T10:05:07Z");
  const s = await makeSeal(KEY, fields, at);
  assert.match(s, /^[0-9a-z]+\.[A-Za-z0-9_-]{43}$/);
  assert.deepEqual(await checkSeal(KEY, fields, s), { sealed: true, at: Math.floor(at / 1000) * 1000 });
  for (const k of Object.keys(fields)) {
    assert.equal((await checkSeal(KEY, { ...fields, [k]: fields[k] + "x" }, s)).sealed, false, k);
  }
  assert.equal((await checkSeal("another-key", fields, s)).sealed, false);
  const [t, sig] = s.split(".");
  assert.equal((await checkSeal(KEY, fields, (parseInt(t, 36) - 1).toString(36) + "." + sig)).sealed, false, "a moved time");
  // one string per seal: a leading zero on the time, or other low bits in the
  // signature's last character, is not this seal
  const last = sig.slice(-1), alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
  const twin = alpha[alpha.indexOf(last) ^ 1];
  for (const bad of ["", "x", s + "A", "zzzzzzzzzz." + sig, t + "." + sig.slice(1) + "!", null, undefined,
                     "0" + t + "." + sig, t + "." + sig.slice(0, -1) + twin]) {
    assert.equal((await checkSeal(KEY, fields, bad)).sealed, false, String(bad));
  }
});
