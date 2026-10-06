// "Your forecast": the page's one address (js/yf-url.js). Both sections and
// the name live in it; each section reads back exactly what it wrote, a write
// by one section never clobbers the other's part, and an old /play/ or /make/
// link (redirected here with its query string by src/worker.js) restores.
//
// Runs on the REAL section 2 context: src/build_make.py's forecast_data(), as
// make.test.mjs does.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import * as PS from "../js/play-state.js";
import * as MS from "../js/make-state.js";
import * as B from "../js/builder-state.js";
import * as YU from "../js/yf-url.js";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../..");
const D = JSON.parse(execFileSync(resolve(repo, ".venv/bin/python"), ["-c",
  "import json, sys; sys.path.insert(0, 'src'); import build_make; print(json.dumps(build_make.forecast_data()))"],
  { cwd: repo, maxBuffer: 1 << 28 }));
const ctx2 = B.contextOf(D.schema);
const REF = D.context_ref;
const start = B.startState(ctx2, { calls: D.start.ward_calls, share: D.start.combined_share }, D.start.ward_calls).state;
const ctx1 = { pools: ["Black African", "Coloured", "Indian/Asian", "White"], polls: ["srf-2026q2-coj", "ipsos-x"],
               laws: ["deduct", "expand", "level", "cap"], cells: [".", "w_bye-0", "w_bye-1"], modelVersion: "cf665663686d0011" };

// Section 1 settings and section 2 forecasts a reader can reach.
const SETTINGS = [
  PS.defaults(ctx1),
  { ...PS.defaults(ctx1), shift: [5, 0, 0, -0.5] },
  { ...PS.defaults(ctx1), polls: ["srf-2026q2-coj"], trust: 45, cell: "w_bye-1" },
  { ...PS.defaults(ctx1), law: "cap" },
];
function forecasts() {
  const out = [{ state: start, coalition: [] }];
  let s = start;
  for (let i = 0; i < 6; i++) {
    s = B.assignWards(s, ctx2, [i * 7], ctx2.codes[(i * 5) % ctx2.codes.length]).state;
    s = B.setPercent(s, ctx2, ctx2.codes[i], 3 + i).state;
    out.push({ state: s, coalition: ctx2.codes.slice(0, i % 3) });
  }
  return out;
}
const NAMES = ["", "Thandi", "Nomvula Dlamini-Khumalo", "<b>x</b>", "Zoë 2026"];

test("both sections and the name survive one address, each part reading only its own", () => {
  let n = 0;
  for (const st of SETTINGS) for (const f of forecasts()) for (const name of NAMES) {
    const q = YU.compose(PS.serialize(st, ctx1), MS.serialize(f, ctx2, REF, start), name);
    const one = PS.parse(YU.partOf(q, YU.ADJUST_KEYS), ctx1);
    assert.deepEqual({ ...one.state, name: "" }, { ...st, name: "" }, q);
    assert.deepEqual(one.dropped, [], q);
    // each section's parser reads the whole address the same as its part
    assert.deepEqual(PS.parse(q, ctx1).state, one.state, q);
    const two = MS.parse(YU.partOf(q, YU.BREAK_KEYS), ctx2, REF, start);
    assert.equal(two.note, null, q);
    assert.deepEqual([two.state.calls, two.state.votes, two.coalition], [f.state.calls, f.state.votes, f.coalition], q);
    assert.deepEqual(MS.parse(q, ctx2, REF, start).state, two.state, q);
    assert.equal(YU.nameOf(q), PS.cleanName(name), q);
    n++;
  }
  assert.equal(n, SETTINGS.length * forecasts().length * NAMES.length);
});

test("a part that writes a key that is not its own is refused, and the check goes quiet without it", () => {
  assert.throws(() => YU.compose("?t=1,0,0,0&f=AAAA", "", ""), /wrote f/);
  assert.throws(() => YU.compose("", "?v=1&t=1", ""), /wrote t/);
  assert.throws(() => YU.compose("?n=x", "", ""), /wrote n/);
  assert.equal(YU.compose("?t=1,0,0,0", "?v=1&c=a&f=AAAA", ""), "?t=1,0,0,0&v=1&c=a&f=AAAA");
  // the two key sets are disjoint, and the name is in neither
  assert.deepEqual(YU.ADJUST_KEYS.filter(k => YU.BREAK_KEYS.includes(k)), []);
  assert.ok(!YU.ADJUST_KEYS.includes(YU.NAME_KEY) && !YU.BREAK_KEYS.includes(YU.NAME_KEY));
});

test("writing one section's part keeps the other's and the name", () => {
  const replaced = [];
  globalThis.location = { pathname: "/your-forecast/", hash: "#break", href: "https://x.test/your-forecast/" };
  globalThis.history = { replaceState: (_s, _t, u) => replaced.push(u) };
  try {
    YU.open("?t=5,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Thandi");
    YU.write("adjust", "?t=2.5,0,0,0&mv=abc");
    assert.equal(replaced.at(-1), "/your-forecast/?t=2.5,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Thandi#break");
    YU.write("break", "");
    assert.equal(replaced.at(-1), "/your-forecast/?t=2.5,0,0,0&mv=abc&n=Thandi#break");
    YU.write("name", "  Sipho  ");
    assert.equal(replaced.at(-1), "/your-forecast/?t=2.5,0,0,0&mv=abc&n=Sipho#break");
    YU.write("adjust", "");
    assert.equal(replaced.at(-1), "/your-forecast/?n=Sipho#break");
    // section 1's share link never carries section 2's part; section 2's carries both
    YU.write("break", "?v=1&c=" + REF + "&f=QUJD");
    YU.write("adjust", "?t=1,0,0,0&mv=abc");
    assert.equal(YU.linkTo("adjust", "#adjust"), "https://x.test/your-forecast/?t=1,0,0,0&mv=abc&n=Sipho#adjust");
    assert.equal(YU.linkTo("break", "#break"), "https://x.test/your-forecast/?t=1,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Sipho#break");
    assert.throws(() => YU.write("other", "?x=1"), /no address part/);
  } finally {
    delete globalThis.location;
    delete globalThis.history;
  }
});

test("a recipient of a shared link never seals under the sharer's name, in either section", () => {
  const replaced = [];
  globalThis.location = { pathname: "/your-forecast/", hash: "", href: "https://x.test/your-forecast/" };
  globalThis.history = { replaceState: (_s, _t, u) => replaced.push(u) };
  try {
    // the arrival a /s/ link opens: section 1's settings, section 2's
    // forecast, the sharer's name and seal
    YU.open("?t=5,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Alice&s=abc.def&from=1");
    assert.equal(YU.currentName(), "Alice", "the address carries the sharer's name");
    assert.equal(YU.sealName(), "", "a sheet would seal under the sharer's name");
    // picking a start drops the arrival and the name together (make.js onChoose)
    YU.write("arrival", "");
    YU.write("name", "");
    assert.equal(YU.sealName(), "");
    // the reader's own name, typed after, is theirs
    YU.write("name", "Thandi");
    assert.equal(YU.sealName(), "Thandi");
    // it can see: the arrival back in the address hides the name again
    YU.write("arrival", "?from=1");
    assert.equal(YU.sealName(), "");
    // a page opened with a name and no arrival is the reader's own
    YU.open("?n=Thandi");
    assert.equal(YU.sealName(), "Thandi");
  } finally {
    YU.open("");
    delete globalThis.location;
    delete globalThis.history;
  }
});

test("an old /play/ link and an old /make/ link restore on the new page", () => {
  // /play/?… as play-state wrote it before 2026-10-03, name included
  const play = "?t=5,0,0,0&p=srf-2026q2-coj&k=50&l=cap&b=w_bye-1&mv=cf665663686d&n=Thandi";
  const one = PS.parse(play, ctx1);
  assert.deepEqual(one.dropped, []);
  assert.deepEqual([one.state.shift, one.state.polls, one.state.trust, one.state.law, one.state.cell],
                   [[5, 0, 0, 0], ["srf-2026q2-coj"], 50, "cap", "w_bye-1"]);
  assert.equal(one.otherVersion, null);
  assert.equal(YU.nameOf(play), "Thandi");
  assert.equal(MS.parse(play, ctx2, REF, start).note, null);          // no section 2 part
  // /make/?… as make-state wrote it, name included
  const f = forecasts().at(-1);
  const make = MS.serialize(f, ctx2, REF, start) + "&n=Sipho";
  const two = MS.parse(make, ctx2, REF, start);
  assert.equal(two.note, null);
  assert.deepEqual([two.state.calls, two.coalition], [f.state.calls, f.coalition]);
  assert.equal(YU.nameOf(make), "Sipho");
  assert.deepEqual(PS.parse(make, ctx1).state, PS.defaults(ctx1));    // no section 1 part
  // the re-composed address writes each back unchanged
  const again = YU.compose(YU.partOf(play, YU.ADJUST_KEYS), YU.partOf(make, YU.BREAK_KEYS), YU.nameOf(play));
  assert.deepEqual(PS.parse(again, ctx1).state, one.state);
  assert.deepEqual(MS.parse(again, ctx2, REF, start).state, two.state);
});

test("a name longer than the limit is refused whole, never cut", () => {
  const long = "x".repeat(PS.NAME_MAX + 1);
  assert.equal(YU.nameOf("?n=" + long), "");
  assert.equal(YU.nameRefused("?n=" + long), true);
  assert.equal(YU.nameOf("?n=" + "x".repeat(PS.NAME_MAX)).length, PS.NAME_MAX);
  assert.equal(YU.nameRefused("?n=" + "x".repeat(PS.NAME_MAX)), false);
  assert.equal(YU.nameRefused(""), false);
  // an empty name is no name, not a refusal
  assert.equal(YU.nameOf("?n=%20%20"), "");
  assert.equal(YU.nameRefused("?n=%20%20"), false);
});

test("a name the blocklist refuses is no name on the page, the return link or the edge (one rule)", async () => {
  const EDGE = await import("../../src/share-edge.js");
  for (const raw of ["IEC Official", "the model", "Ｏｆｆｉｃｉａｌ", "WhySoSerious"]) {
    assert.equal(PS.cardName(raw), "", raw);
    assert.equal(PS.nameBlocked(raw), true, raw);
    assert.equal(YU.nameOf("?n=" + encodeURIComponent(raw)), "", raw);
    assert.equal(EDGE.cardName(raw), "", raw);
    assert.equal(YU.friendPart("AAAA", raw), "?vs=AAAA", raw);
    assert.equal(YU.compose("", "", raw), "", raw);
  }
  YU.open("?vs=AAAA&vn=" + encodeURIComponent("IEC Official"));
  assert.deepEqual(YU.friend(), { f: "AAAA", name: "" });
  // the check sees: an ordinary name passes every one of them
  assert.equal(PS.cardName("Thandi"), "Thandi");
  assert.equal(PS.nameBlocked("Thandi"), false);
  assert.equal(PS.nameBlocked(""), false);
  assert.equal(YU.nameOf("?n=Thandi"), "Thandi");
  YU.open("");
});

test("in the page, the address it opened with is the first state of every part", async () => {
  // A fresh copy of the module, imported with an address in place, as the
  // browser imports it: the first write by one section keeps the other's
  // part and the name (an old /play/ link's name, a /make/ link's forecast
  // while section 2 is still loading).
  const replaced = [];
  globalThis.location = { pathname: "/your-forecast/", hash: "", href: "https://x.test/your-forecast/",
                          search: "?t=5,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Thandi" };
  globalThis.history = { replaceState: (_s, _t, u) => replaced.push(u) };
  try {
    const fresh = await import("../js/yf-url.js?fresh=1");
    assert.equal(fresh.currentName(), "Thandi");
    fresh.write("adjust", "?t=2,0,0,0&mv=abc");
    assert.equal(replaced.at(-1), "/your-forecast/?t=2,0,0,0&mv=abc&v=1&c=" + REF + "&f=QUJD&n=Thandi");
    // it can see: the module imported with no address starts empty
    delete globalThis.location;
    const bare = await import("../js/yf-url.js?fresh=2");
    assert.equal(bare.currentName(), "");
  } finally {
    delete globalThis.location;
    delete globalThis.history;
  }
});
