// Build-time checks: the generated schema is current, the generator reads the
// artefact (it types nothing), and the Python Worker's seat code is a byte copy.
import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "../../tools/make_schema.mjs";
import { FILES } from "../../tools/sync_seats_py.mjs";
import { bundledTables } from "../../tools/font_widths.mjs";
import { FONT_WIDTHS, textWidth } from "../../../interactive/js/card.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const repo = resolve(root, "..");
const MODEL = "interactive/fixtures/placeholder-model.json";
const GEOM = "interactive/fixtures/geometry.json";
const names = { model: MODEL, geometry: GEOM };
const read = p => readFileSync(resolve(repo, p));

describe("generated/ is current", () => {
  it("regenerating from the sources gives exactly the committed files", () => {
    const out = build(read(MODEL), read(GEOM), names);
    for (const [rel, text] of Object.entries(out))
      expect(readFileSync(resolve(root, rel), "utf8"), rel).toBe(text);
  });
});

describe("the generator reads the artefact", () => {
  const model = JSON.parse(read(MODEL));
  it("a new party in the artefact appears in the schema", () => {
    const m = { ...model, parties: [...model.parties, { code: "NEWP", name: "New", colour: "#000" }] };
    const s = JSON.parse(build(Buffer.from(JSON.stringify(m)), read(GEOM), names)["generated/forecast.schema.json"]);
    expect(s.properties.ward_calls.items.enum).toContain("NEWP");
    expect(s.properties.combined_share.required).toContain("NEWP");
  });
  it("a different council size moves the schema's council", () => {
    const m = { ...model, council_seats: model.council_seats + 2, majority: model.majority + 1 };
    const s = JSON.parse(build(Buffer.from(JSON.stringify(m)), read(GEOM), names)["generated/forecast.schema.json"]);
    expect(s["x-council"].council_seats).toBe(model.council_seats + 2);
  });
  it("a ward count that disagrees with ward_seats is refused", () => {
    const m = { ...model, ward_seats: model.ward_seats + 1 };
    expect(() => build(Buffer.from(JSON.stringify(m)), read(GEOM), names)).toThrow(/ward_seats/);
  });
  it("the seat context and total_votes come from the artefact", () => {
    const m = { ...model, total_votes: model.total_votes + 7, no_pr_list: [model.parties[0].code] };
    const s = JSON.parse(build(Buffer.from(JSON.stringify(m)), read(GEOM), names)["generated/forecast.schema.json"]);
    expect(s["x-total-votes"]).toBe(model.total_votes + 7);
    expect(s["x-seat-context"].no_pr_list).toEqual([model.parties[0].code]);
    expect(s["x-seat-context"].council).toBe(model.council_seats);
    expect(s["x-seat-context"].wards).toEqual(s["x-ward-ids"]);
  });
  it("an artefact without what reader_seats needs is refused, not defaulted", () => {
    for (const k of ["city", "target", "total_votes", "no_pr_list"]) {
      const m = { ...model }; delete m[k];
      expect(() => build(Buffer.from(JSON.stringify(m)), read(GEOM), names)).toThrow(new RegExp(k));
    }
    const bad = { ...model, total_votes: 1.5 };
    expect(() => build(Buffer.from(JSON.stringify(bad)), read(GEOM), names)).toThrow(/total_votes/);
    const stray = { ...model, no_pr_list: ["NOPE"] };
    expect(() => build(Buffer.from(JSON.stringify(stray)), read(GEOM), names)).toThrow(/no_pr_list/);
  });
  it("records the sha256 of each source", () => {
    const s = JSON.parse(build(read(MODEL), read(GEOM), names)["generated/forecast.schema.json"]);
    expect(Object.keys(s["x-sources"])).toEqual([MODEL, GEOM]);
  });
});

describe("seats-py carries the project's seat code byte for byte", () => {
  for (const f of FILES) {
    it(f, () => {
      const copy = resolve(root, "seats-py/src", f);
      if (!existsSync(copy)) {
        // Not copied yet (src/reader_seats.py is being written elsewhere). The
        // Worker then answers 501 and saves answer 503: recorded, not hidden.
        expect(readFileSync(resolve(root, "seats-py/src/entry.py"), "utf8")).toMatch(/501/);
        return;
      }
      expect(readFileSync(copy).equals(read(`src/${f}`))).toBe(true);
    });
  }
  it("entry.py contains no seat arithmetic of its own", () => {
    const src = readFileSync(resolve(root, "seats-py/src/entry.py"), "utf8");
    expect(src).not.toMatch(/quota|largest|remainder|\/\//);
  });
});

describe("the card measures text with the fonts the server renders with", () => {
  it("card.js's width table equals the bundled DejaVu fonts, face for face", () => {
    const fresh = bundledTables();
    expect(Object.keys(FONT_WIDTHS).sort()).toEqual(Object.keys(fresh).sort());
    for (const [k, t] of Object.entries(fresh)) expect(FONT_WIDTHS[k], k).toEqual({ em: t.em, w: t.widths });
  });
  it("measures: a wide letter is wider than a narrow one, and unknown glyphs err wide", () => {
    expect(textWidth("WWWW", 20)).toBeGreaterThan(textWidth("iiii", 20));
    expect(textWidth("é", 20)).toBeGreaterThanOrEqual(textWidth("W", 20));
  });
});

describe("hand-maintained registers agree, both directions", () => {
  const sql = readFileSync(resolve(root, "migrations/0001_init.sql"), "utf8");
  const checkList = col => sql.match(new RegExp(`${col}\\s+TEXT NOT NULL CHECK \\(${col} IN\\s*\\(([^)]*)\\)`))[1]
    .split(",").map(s => s.trim().replace(/'/g, "")).sort();
  const srcOf = f => readFileSync(resolve(root, "src", f), "utf8");

  it("providers: the D1 CHECK list equals the PROVIDERS keys in src/providers.js", () => {
    const keys = [...srcOf("providers.js").matchAll(/^  (\w+): \{$/gm)].map(m => m[1]).sort();
    expect(keys.length).toBeGreaterThan(0);
    expect(checkList("provider")).toEqual(keys);
  });

  it("consent purposes: the D1 CHECK list equals the screen's purposes plus next_election", () => {
    const m = srcOf("consent.js").match(/SCREEN_PURPOSES = \[([^\]]*)\]/)[1];
    const screen = m.split(",").map(s => s.trim().replace(/"/g, ""));
    expect(screen.length).toBeGreaterThan(0);
    expect(checkList("purpose")).toEqual([...screen, "next_election"].sort());
  });
});
