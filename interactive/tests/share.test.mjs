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
  // a name typed as a possessive takes no second one
  assert.equal(SC.cardTitle("Simon's"), "Simon's Election Forecast");
  assert.equal(SC.cardTitle("Simon’s"), "Simon’s Election Forecast");
  assert.equal(SC.cardTitle("the Joneses'"), "the Joneses' Election Forecast");
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
  const rowBands = svg => [...svg.matchAll(new RegExp(`<rect x="[\\d.]+" y="[\\d.]+" width="[\\d.]+" height="${SC.LINK_PITCH - 4}" fill="([^"]+)"`, "g"))].map(m => m[1]);
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

test("words on a band read at 3:1 or better: every roster colour and every pair, else they sit on paper plates", () => {
  // the colours the cards paint: each roster colour as markColour marks it
  const roster = [...new Set(Object.values(FIXTURE.parties).map(p => p.colour.toLowerCase()))];
  const colours = [...new Set(roster.map(SC.markColour))];
  assert.ok(colours.some(c => !roster.includes(c)), "the scan sees the ink a colourless winner is marked in");
  const pairs = colours.flatMap((c, i) => colours.slice(i + 1).map(d => [c, d]));
  assert.ok(colours.length > 5 && pairs.length > 10, "the scan looked at the roster");
  // a colour the card cannot read is marked in the ink, never thrown on
  for (const odd of ["red", "#abc", "", null, undefined, "#zzzzzz"]) assert.equal(SC.markColour(odd), SC.markColour("#8b918b"), String(odd));
  let plated = 0;
  for (const fills of [...colours.map(c => [c]), ...pairs]) {
    const b = SC.bandInk(fills);
    assert.ok(b.ratio >= SC.BAND_MIN_CONTRAST, fills.join(" "));
    if (b.plated) plated++;
    else assert.equal(b.ink, SC.inkOn(fills), fills.join(" "));
  }
  // a tie between two colours that no ink reads on: the headline goes on a
  // plate (two hued colours: a colour with no hue is marked in the ink)
  const [c, d] = pairs.find(f => SC.bandInk(f).plated && f.every(x => SC.markColour(x) === x)) || [];
  assert.ok(c, "some pair of roster colours needs a plate");
  const [p, q] = [A.rows[0], A.rows[1]];
  const recolour = code => code === p.code ? { ...party(code), colour: c } : code === q.code ? { ...party(code), colour: d } : party(code);
  const answer = { ...FIXTURE.A.answer, seats: { ...FIXTURE.A.answer.seats, [q.code]: p.seats } };
  const tie = SC.forecastSpec({ name: "T", answer, outcome: { ...A.outcome, largest: null }, vote: FIXTURE.A.vote,
    calls: A.calls, party: recolour, baseline: FIXTURE.baseline, election: FIXTURE.election });
  const paper = /<rect [^>]*fill="([^"]+)"/.exec(SC.linkCardSVG(tie, ASSETS, recolour))[1];   // the card's ground
  for (const [svg, headY] of [[SC.linkCardSVG(tie, ASSETS, recolour), SC.LINK_HEAD_Y], [SC.storyCardSVG(tie, ASSETS, recolour), SC.STORY_HEAD_Y],
    [SC.duelCardSVG(tie, tie, ASSETS, recolour), SC.DUEL_HEAD_Y]]) {
    const plates = [...svg.matchAll(new RegExp(`<rect x="[\\d.]+" y="([\\d.]+)" width="[\\d.]+" height="([\\d.]+)" fill="${paper}" rx=`, "g"))];
    assert.ok(plates.some(m => Number(m[1]) < headY && Number(m[1]) + Number(m[2]) > headY), "a plate under the headline");
  }
  // one roster colour alone never needs a plate
  for (const F of [A, Bspec]) assert.ok(!SC.bandInk([F.rows[0].colour]).plated);
});

test("the brand on a card holds no CSS variable, which resvg cannot read: every part in the card's ink", () => {
  const svg = readFileSync(resolve(repo, "site/logo.svg"), "utf8");
  assert.ok(/currentColor/.test(svg), "the site's logo is drawn in currentColor, so the check can see it");
  assert.ok(!/var\(|currentColor/.test(SC.brandOf(svg).body));
  // a part in a page token (var(--ink-3, currentColor)) is resolved too:
  // constructed, since the logo carries none
  const muted = svg.replace("</svg>", '<path style="fill:var(--ink-3,currentColor)" d="M0 0h1v1z"/></svg>');
  assert.ok(/var\(--/.test(muted));
  assert.ok(!/var\(|currentColor/.test(SC.brandOf(muted).body));
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
  const files = ["js/share-card.js", "js/share-sheet.js", "js/make-share.js", "js/play-share.js", "js/arrival.js"].map(f => [f, readFileSync(resolve(here, "..", f), "utf8")]);
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
  // the badge words (reweight.BOLDNESS) and the retired ones
  for (const [f, text] of files) for (const w of ["Safe bet", "Steady as she goes", "Long shot", "Wild call", "Hail Mary", "Safe call", "Bold call"])
    assert.ok(!text.includes(w), `${f} types ${w}`);
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
    if (r.code in FIXTURE.baseline.list_vote) {
      assert.equal(r.seatsVs, SC.signed(r.seats - (FIXTURE.baseline.seats[r.code] || 0)));
      assert.match(r.voteVs, /^[+\u2212\u00b1]\d+\.\d$/);
      // list against list: the card's vote is the list ballot, and so is the baseline's
      assert.equal(r.voteVs, SC.signed(FIXTURE.A.vote[r.code] - FIXTURE.baseline.list_vote[r.code], 1));
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

test("a winner with no colour of its own is marked in the card's ink, on the band and its row, and reads", () => {
  const grey = Object.values(FIXTURE.parties).map(p => p.colour).find(c => SC.markColour(c) !== c);
  assert.ok(grey, "the roster has a colour with no hue");
  const hued = A.rows[0].colour;
  assert.equal(SC.markColour(hued), hued, "a hued colour is its own mark");
  const top = A.rows[0].code;
  const recolour = code => (code === top ? { ...party(code), colour: grey } : party(code));
  const F = SC.forecastSpec({ name: "T", answer: FIXTURE.A.answer, outcome: A.outcome, vote: FIXTURE.A.vote, calls: A.calls,
    party: recolour, baseline: FIXTURE.baseline, election: FIXTURE.election });
  const svg = SC.linkCardSVG(F, ASSETS, recolour);
  const band = [...svg.matchAll(new RegExp(`<rect x="[\\d.]+" y="0" width="[\\d.]+" height="${SC.LINK_BAND}" fill="([^"]+)"`, "g"))].map(m => m[1]);
  assert.equal(band.length, 1);
  assert.notEqual(band[0], grey, "the winner's band is the grey");
  assert.equal(band[0], SC.markColour(grey));
  assert.ok(SC.bandInk(band).ratio >= SC.BAND_MIN_CONTRAST);
  const rowBands = [...svg.matchAll(new RegExp(`<rect x="[\\d.]+" y="[\\d.]+" width="[\\d.]+" height="${SC.LINK_PITCH - 4}" fill="([^"]+)"`, "g"))].map(m => m[1]);
  assert.deepEqual(rowBands, [SC.markColour(grey)]);
  // it can see: with the party's own colour the band is that colour
  assert.ok(SC.linkCardSVG(A, ASSETS, party).includes(`height="${SC.LINK_BAND}" fill="${hued}"`));
});

// The right edge of every left-anchored text, measured in the face that
// draws it; a clipped text (a name in its column) is held by its clip instead.
function rightEdges(svg) {
  const out = [];
  for (const m of svg.matchAll(/<text x="([\d.-]+)" y="[\d.-]+" font-family="([^"]+)" font-weight="(\d+)" font-size="([\d.]+)"([^>]*)>([^<]*)<\/text>/g)) {
    if (/text-anchor|clip-path/.test(m[5])) continue;
    const face = m[2] === "IBM Plex Serif" ? "serifSemi" : m[2] === "IBM Plex Mono" ? "monoSemi" : { 400: "sans", 600: "sansSemi", 700: "sansBold" }[m[3]];
    const t = m[6].replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&amp;/g, "&");
    out.push({ text: t, right: Number(m[1]) + SC.textWidth(t, Number(m[4]), face) });
  }
  return out;
}

// Each name's clip box, and the left edge of the first figure drawn after it
// on its row: a name may not reach the figure beside it.
function nameClips(svg) {
  const out = [];
  for (const m of svg.matchAll(/<clipPath id="([\w-]+)"><rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"/g)) {
    const after = svg.slice(m.index + m[0].length);
    const fig = /<text x="([\d.]+)" y="[\d.]+" font-family="[^"]+" font-weight="(\d+)" font-size="([\d.]+)" text-anchor="end"[^>]*>([^<]*)<\/text>/.exec(after);
    const face = { 400: "sans", 600: "sansSemi", 700: "sansBold" }[fig[2]];
    out.push({ id: m[1], right: Number(m[2]) + Number(m[3]), figLeft: Number(fig[1]) - SC.textWidth(fig[4], Number(fig[3]), face), fig: fig[4] });
  }
  return out;
}

test("a long party name is fitted and clipped to its column, never into the figures, on every card", () => {
  const long = A.rows[1].code;
  const named = code => (code === long ? { ...party(code), name: "National Democratic Convention of the Very Long Name" } : party(code));
  const F = SC.forecastSpec({ name: "T", answer: FIXTURE.A.answer, outcome: A.outcome, vote: FIXTURE.A.vote, calls: A.calls,
    party: named, baseline: FIXTURE.baseline, election: FIXTURE.election });
  // every governing party long-named too: the governing lines must fit
  assert.ok(F.coalition.length >= 1, "the fixture's forecast has a coalition");
  const gov = new Set(F.coalition);
  const govNamed = code => (gov.has(code) || code === long ? { ...party(code), name: "National Democratic Convention of the Very Long Name " + code } : party(code));
  const FG = SC.forecastSpec({ name: "T", answer: FIXTURE.A.answer, outcome: A.outcome, vote: FIXTURE.A.vote, calls: A.calls,
    party: govNamed, baseline: FIXTURE.baseline, election: FIXTURE.election });
  for (const [what, svg] of [["link", SC.linkCardSVG(FG, ASSETS, govNamed)], ["story", SC.storyCardSVG(FG, ASSETS, govNamed)]]) {
    const [W] = SC.SIZES[what];
    assert.ok(svg.includes("Governing"), what);
    for (const t of rightEdges(svg)) assert.ok(t.right <= W - 8, `${what}: "${t.text}" ends at ${t.right.toFixed(0)}`);
  }
  // it can see: a governing line typed at full size off the card is caught
  const off = SC.linkCardSVG(FG, ASSETS, govNamed).replace("</svg>",
    `<text x="900" y="300" font-family="IBM Plex Sans" font-weight="600" font-size="20" fill="#fff">${"National Democratic Convention ".repeat(3)}</text></svg>`);
  assert.ok(rightEdges(off).some(t => t.right > SC.SIZES.link[0] - 8));
  const G = SC.forecastSpec({ name: "U", answer: FIXTURE.B.answer, outcome: Bspec.outcome, vote: FIXTURE.B.vote, calls: Bspec.calls,
    party: named, baseline: FIXTURE.baseline, election: FIXTURE.election });
  for (const [what, svg, n] of [["link", SC.linkCardSVG(F, ASSETS, named), SC.listedRows(F, SC.ROWS.link).length],
    ["story", SC.storyCardSVG(F, ASSETS, named), SC.listedRows(F, SC.ROWS.story).length], ["duel", SC.duelCardSVG(F, G, ASSETS, named), 2]]) {
    const clips = nameClips(svg);
    assert.ok(clips.length >= n, `${what}: ${clips.length} names clipped`);
    for (const c of clips) assert.ok(c.right <= c.figLeft - 4, `${what} ${c.id}: the name's box ends at ${c.right}, the figure "${c.fig}" starts at ${c.figLeft}`);
    assert.ok(svg.includes("National Dem"), what);
    // no words run off the card: the governing line included
    const [W] = SC.SIZES[what];
    for (const t of rightEdges(svg)) assert.ok(t.right <= W - 8, `${what}: "${t.text}" ends at ${t.right.toFixed(0)}`);
    // the clip is applied to the name's text
    for (const c of clips) assert.ok(svg.includes(`clip-path="url(#${c.id})"`), `${what} ${c.id}`);
  }
  // it can see: a clip box widened into the figure is caught
  const svg = SC.linkCardSVG(F, ASSETS, named), c = nameClips(svg)[0];
  const wide = svg.replace(new RegExp(`(<clipPath id="${c.id}"><rect x="[\\d.]+" y="[\\d.]+" width=")([\\d.]+)`), (m, a, w) => a + (Number(w) + 200));
  assert.ok(nameClips(wide).some(x => x.right > x.figLeft - 4));
});

// The map's drawn width (from its group's scale) and the lowest baseline.
function space(svg) {
  const m = /<g transform="translate\([\d.]+ [\d.]+\) scale\(([\d.]+)\)">/.exec(svg);
  return { mapW: m ? FIXTURE.geometry.W * Number(m[1]) : 0, lowest: Math.max(...[...svg.matchAll(/<text x="[\d.]+" y="([\d.]+)"/g)].map(x => Number(x[1]))) };
}
function unused(svg, size) {
  const [W, H] = SC.SIZES[size], sp = space(svg), out = [];
  const least = (size === "story" ? SC.READER_STORY_MAP_MIN_SHARE : SC.LINK_MAP_MIN_SHARE) * W;
  if (!(sp.mapW >= least)) out.push(`map ${sp.mapW.toFixed(0)} px wide, under ${least.toFixed(0)}`);
  if (size === "story" && !(sp.lowest >= SC.STORY_TEXT_BOTTOM - SC.STORY_FILL_SLACK && sp.lowest <= SC.STORY_TEXT_BOTTOM)) out.push(`lowest words at ${sp.lowest}`);
  if (size === "link" && !(sp.lowest <= H - 10)) out.push(`words at ${sp.lowest} run off the card`);
  return out;
}

test("every reader's card carries the council graphic, the table, the map and the logo, and uses the canvas", () => {
  for (const F of [A, Bspec, { ...Bspec, excess: [A.excess[0] || "x", "A second long note about wards and seats that wraps."] }]) {
    for (const [size, svg] of [["link", SC.linkCardSVG(F, ASSETS, party)], ["story", SC.storyCardSVG(F, ASSETS, party)]]) {
      assert.deepEqual(unused(svg, size), [], size);
      assert.ok(svg.includes(F.majority + " for a majority"), size + ": the council graphic");
      assert.ok(svg.includes(">% of<"), size + ": the table");
      assert.ok(svg.includes(`viewBox="${ASSETS.brand.viewBox}"`), size + ": the logo");
      const m = /<g transform="translate\([\d.]+ [\d.]+\) scale\([\d.]+\)">([\s\S]*?)<\/g>/.exec(svg);
      assert.equal((m[1].match(/<path /g) || []).length, FIXTURE.geometry.wards.length, size + ": every ward");
    }
  }
  // it can see: a map at half the scale, and a story card cut short
  const svg = SC.storyCardSVG(A, ASSETS, party);
  const small = svg.replace(/(<g transform="translate\([\d.]+ [\d.]+\) scale\()([\d.]+)/, (m, a, k) => a + (k / 2).toFixed(4));
  assert.equal(unused(small, "story").length, 1);
  const cut = svg.replace(/<text x="[\d.]+" y="(1[5-6]\d\d(?:\.\d)?)"[^>]*>[^<]*<\/text>/g, "");
  assert.ok(unused(cut, "story").some(w => w.startsWith("lowest")));
  assert.deepEqual(unused(svg, "story"), []);
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
const stateA = B.stateFromPrediction(ctx, { ward_calls: FIXTURE.A.calls, ward_votes: FIXTURE.A.ward_votes,
                                            list_votes: FIXTURE.A.list_votes });
const fA = MS.encode(stateA, FIXTURE.A.coalition, ctx);
const KEY = "test-only-seal-key";

function fakeEnv({ seats = true, key = KEY } = {}) {
  const files = { "/your-forecast/forecast.json": JSON.stringify(D),
    "/your-forecast/parties.json": JSON.stringify(FIXTURE.parties),
    "/logo.svg": readFileSync(resolve(repo, "site/logo.svg"), "utf8") };
  const logos = new Set(readdirSync(resolve(repo, "site/logos")));
  const stamps = new Set(readdirSync(resolve(repo, "src/stamps")));
  const asked = [];
  return { asked, env: {
    ...(key ? { SEAL_KEY: key } : {}),
    ASSETS: { async fetch(req) {
      const p = new URL(req.url).pathname;
      if (files[p]) return new Response(files[p], { status: 200 });
      const m = /^\/logos\/(.+)$/.exec(p);
      if (m && logos.has(m[1])) return new Response(readFileSync(resolve(repo, "site/logos", m[1])), { status: 200 });
      // the owner's badges, served at /stamps/ from src/stamps/ (site_assets)
      const st = /^\/stamps\/(reader-[a-z-]+\.svg)$/.exec(p);
      if (st && stamps.has(st[1])) return new Response(readFileSync(resolve(repo, "src/stamps", st[1]), "utf8"), { status: 200 });
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
  const fields = { v: MS.FORMAT, c: D.context_ref, f: fA, n: "Thandi" };
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
  // the owner's badge for the outcome's words, embedded with its ids prefixed, and the call it judges
  const badge = SC.stampOf(readFileSync(resolve(repo, "src/stamps", SC.badgeFile(FIXTURE.A.answer.outcome.badge)), "utf8"));
  assert.ok(svg.includes(SC.prefixIds(badge.body, "lb")));
  assert.ok(FIXTURE.A.answer.outcome.boldest.party && svg.includes(">Boldest call: "));
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

test("section 1's hand-off, a start with no coalition, is a forecast the edge and the seal read unchanged", async () => {
  // make.js setHandoff encodes the hand-off (B.stateFromPrediction of page.py's
  // handoff) with no coalition; src/share-edge.js decodeLink must read it as it
  // reads section 2's
  EDGE.forgetPageData();
  const PD = await EDGE.pageData(fakeEnv().env, new URL("https://joburg.whysoserious.city/"));
  const f = MS.encode(stateA, [], ctx);
  const read = EDGE.decodeLink(MS.FORMAT, D.context_ref, f, PD);
  assert.ok(read, "the hand-off's link is not read");
  assert.deepEqual(read.coalition, []);
  assert.deepEqual(read.state.calls, stateA.calls);
  // it can see: another context is refused
  assert.equal(EDGE.decodeLink(MS.FORMAT, "another-context", f, PD), null);
});

test("an answer that breaks the seat law's arithmetic draws no card", async () => {
  EDGE.forgetPageData();
  const { env } = fakeEnv();
  const bad = { ...env, SEATS: { async fetch() {
    const a = FIXTURE.A.answer;
    const k = Object.keys(a.seats)[0];
    return new Response(JSON.stringify({ ...a, seats: { ...a.seats, [k]: a.seats[k] + 5 }, code_ref: "ab".repeat(32), draws_sha256: D.draws_sha256 }), { status: 200 });
  } } };
  const q = new URLSearchParams({ v: MS.FORMAT, c: D.context_ref, f: fA }).toString();
  await assert.rejects(EDGE.cardFor(new URL("https://joburg.whysoserious.city/og/1/link.png?" + q), bad, "link"));
});

// ---------- the seal ----------

test("a seal made under an earlier context still checks; the answer says the page cannot read it", async () => {
  EDGE.forgetPageData();
  const fields = { v: MS.FORMAT, c: "an-earlier-context", f: fA, n: "Thandi" };
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
