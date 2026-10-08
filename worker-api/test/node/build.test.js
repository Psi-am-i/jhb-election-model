// Build-time checks: the generated geometry is current, the schema generator
// reads the artefact (it types nothing), and the Python Worker's seat code is a
// byte copy.
import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { build, geometryOf } from "../../tools/make_schema.mjs";
import { FORMAT } from "../../../interactive/js/make-state.js";
import { ALL as FILES, checkCopy, copy } from "../../tools/sync_seats_py.mjs";
import { SCREEN_PURPOSES } from "../../../interactive/js/consent-terms.js";
import { mkdtempSync, writeFileSync, rmSync, unlinkSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { bundledTables } from "../../tools/font_widths.mjs";
import { FONT_WIDTHS, textWidth } from "../../../interactive/js/card.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const repo = resolve(root, "..");
const MODEL = "interactive/fixtures/placeholder-model.json";
const GEOM = "interactive/fixtures/geometry.json";
const names = { model: MODEL, geometry: GEOM };
const read = p => readFileSync(resolve(repo, p));

// The artefact build_make writes carries the editor's bounds; the prototype's
// placeholder fixture has none, so the test adds them: equal ward shares over
// the geometry's wards and four finite bounds. Constructed, not measured.
const geomWards = JSON.parse(read(GEOM)).wards.map(w => String(w.id));
const withBounds = m => ({ ...m, editor_bounds: { e: Object.fromEntries(geomWards.map(w => [w, 1 / geomWards.length])),
  q_win: 0.2, q_run: 0.5, gap_min: -5, gap_max: 10 } });
const schemaOf = m => build(Buffer.from(JSON.stringify(m)), read(GEOM), names).schema;

describe("generated/geometry.json is current", () => {
  it("regenerating from the source gives exactly the committed file", () => {
    const g = geometryOf(read(GEOM), GEOM);
    expect(readFileSync(resolve(root, "generated/geometry.json"), "utf8")).toBe(JSON.stringify(g) + "\n");
  });
  it("the retired placeholder schema is not there (guard G13)", () => {
    expect(existsSync(resolve(root, "generated/forecast.schema.json"))).toBe(false);
  });
});

describe("the generator reads the artefact", () => {
  const model = withBounds(JSON.parse(read(MODEL)));
  it("the entry version is make-state.js FORMAT, the one definition", () => {
    expect(schemaOf(model).properties.v.const).toBe(FORMAT);
  });
  it("a new party in the artefact appears in the schema, on both ballots", () => {
    const m = { ...model, parties: [...model.parties, { code: "NEWP", name: "New", colour: "#000" }] };
    const s = schemaOf(m);
    expect(s.properties.ward_calls.items.enum).toContain("NEWP");
    expect(s.properties.ward_votes.required).toContain("NEWP");
    expect(s.properties.list_votes.required).toContain("NEWP");
  });
  it("a different council size moves the schema's council", () => {
    const m = { ...model, council_seats: model.council_seats + 2, majority: model.majority + 1 };
    expect(schemaOf(m)["x-council"].council_seats).toBe(model.council_seats + 2);
  });
  it("a ward count that disagrees with ward_seats is refused", () => {
    const m = { ...model, ward_seats: model.ward_seats + 1 };
    expect(() => schemaOf(m)).toThrow(/ward_seats/);
  });
  it("the seat context and the editor's bounds come from the artefact; no total is carried", () => {
    const m = { ...model, no_pr_list: [model.parties[0].code] };
    const s = schemaOf(m);
    expect(s["x-seat-context"].no_pr_list).toEqual([model.parties[0].code]);
    expect(s["x-seat-context"].council).toBe(model.council_seats);
    expect(s["x-seat-context"].wards).toEqual(s["x-ward-ids"]);
    expect(s["x-editor-bounds"]).toEqual(m.editor_bounds);
    expect(s["x-total-votes"]).toBeUndefined();
    expect(s["x-share-sum"]).toBeUndefined();
  });
  it("an artefact without what reader_seats and the editor need is refused, not defaulted", () => {
    for (const k of ["city", "target", "no_pr_list", "editor_bounds"]) {
      const m = { ...model }; delete m[k];
      expect(() => schemaOf(m)).toThrow(new RegExp(k));
    }
    const stray = { ...model, no_pr_list: ["NOPE"] };
    expect(() => schemaOf(stray)).toThrow(/no_pr_list/);
    const short = { ...model, editor_bounds: { ...model.editor_bounds, e: { [geomWards[0]]: 1 } } };
    expect(() => schemaOf(short)).toThrow(/editor bounds/);
  });
  it("records the sha256 of each source", () => {
    expect(Object.keys(schemaOf(model)["x-sources"])).toEqual([MODEL, GEOM]);
  });
});

describe("seats-py carries the project's seat code byte for byte", () => {
  // R5 finding 16: a missing copy is a failure, not a skip. Run
  // `npm run sync:seats` on a fresh clone.
  for (const f of FILES) {
    it(f, () => {
      const copy = resolve(root, "seats-py/src", f);
      expect(existsSync(copy), `seats-py/src/${f} not copied: run npm run sync:seats`).toBe(true);
      expect(readFileSync(copy).equals(read(`src/${f}`))).toBe(true);
    });
  }
  it("the live copy passes the check", () => expect(checkCopy()).toEqual([]));
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
    // The list lives in interactive/js/consent-terms.js, which the page and
    // src/consent.js both import.
    expect(SCREEN_PURPOSES.length).toBeGreaterThan(0);
    expect(checkList("purpose")).toEqual([...SCREEN_PURPOSES, "next_election"].sort());
  });
});

describe("sync_seats_py --check fails on a partial or missing copy (R5 finding 16)", () => {
  // Constructed trees: a source dir holding FILES, and a destination built from it.
  function tree() {
    const base = mkdtempSync(resolve(tmpdir(), "seatsync-"));
    const src = resolve(base, "src"), dst = resolve(base, "dst");
    execFileSync("mkdir", ["-p", src, dst]);
    FILES.forEach((f, i) => writeFileSync(resolve(src, f), `# ${f} ${i}\n`));
    return { base, src, dst };
  }
  it("a complete copy passes", () => {
    const t = tree(); copy(t.src, t.dst);
    expect(checkCopy(t.src, t.dst)).toEqual([]);
    rmSync(t.base, { recursive: true });
  });
  it("a copy with no files at all fails, once per file and for code_ref.py", () => {
    const t = tree();
    const p = checkCopy(t.src, t.dst);
    expect(p.filter(x => /^not copied/.test(x)).length).toBe(FILES.length);
    expect(p).toContain("not written: seats-py/src/code_ref.py");
    rmSync(t.base, { recursive: true });
  });
  it("a partial copy fails (the old check passed it), and passes again when completed", () => {
    const t = tree(); copy(t.src, t.dst);
    unlinkSync(resolve(t.dst, FILES[3]));
    expect(checkCopy(t.src, t.dst)).toEqual([`not copied: seats-py/src/${FILES[3]}`]);
    copy(t.src, t.dst);
    expect(checkCopy(t.src, t.dst)).toEqual([]);
    rmSync(t.base, { recursive: true });
  });
  it("a changed source fails the file and code_ref.py", () => {
    const t = tree(); copy(t.src, t.dst);
    writeFileSync(resolve(t.src, FILES[0]), "# edited\n");
    const p = checkCopy(t.src, t.dst);
    expect(p).toContain(`STALE: seats-py/src/${FILES[0]} differs from src/${FILES[0]}`);
    expect(p.some(x => /code_ref\.py does not name/.test(x))).toBe(true);
    rmSync(t.base, { recursive: true });
  });
});

describe("every copied Python file is gitignored, and only those (R5 finding 16)", () => {
  const ignored = rel => {
    try { execFileSync("git", ["check-ignore", "-q", "--no-index", rel], { cwd: root }); return true; }
    catch (e) { if (e.status === 1) return false; throw e; }
  };
  const copied = [...FILES, "code_ref.py"].map(f => `seats-py/src/${f}`);
  it("the population is the tool's FILES plus code_ref.py", () => {
    expect(copied.length).toBe(FILES.length + 1);
    expect(FILES.length).toBeGreaterThan(0);
  });
  for (const rel of copied) it(`${rel} is ignored`, () => expect(ignored(rel)).toBe(true));
  it("entry.py, which is written here, is not ignored", () => expect(ignored("seats-py/src/entry.py")).toBe(false));
  it("the detector can see: a file outside seats-py/src is not ignored", () => expect(ignored("src/index.js")).toBe(false));
  it("nothing in seats-py/src other than entry.py and the copies is expected", () => {
    const present = readdirSync(resolve(root, "seats-py/src")).filter(f => f.endsWith(".py"));
    for (const f of present) expect(["entry.py", "code_ref.py", ...FILES], f).toContain(f);
  });
});

describe("request logs carry no tokens (R5 finding 10)", () => {
  const cfg = readFileSync(resolve(root, "wrangler.jsonc"), "utf8");
  it("invocation logs are off (they record the URL, and OAuth codes arrive in it)", () => {
    expect(cfg).toMatch(/"observability":\s*\{[^}]*"logs":\s*\{\s*"invocation_logs":\s*false\s*\}/);
  });
  it("no source file logs a request URL", () => {
    for (const f of readdirSync(resolve(root, "src"))) {
      const t = readFileSync(resolve(root, "src", f), "utf8");
      for (const line of t.split("\n").filter(l => /console\.(log|error|warn)/.test(l)))
        expect(line, `${f}: ${line.trim()}`).not.toMatch(/request\.url|\burl\b|\.search|searchParams/);
    }
  });
});

describe("configuration", () => {
  const cfg = readFileSync(resolve(root, "wrangler.jsonc"), "utf8");
  const varsBlocks = [...cfg.matchAll(/"vars":\s*\{([^}]*)\}/g)].map(m => [...m[1].matchAll(/"([A-Z_]+)":/g)].map(x => x[1]).sort());
  it("the top-level and dev vars name the same settings (vars are not inherited)", () => {
    expect(varsBlocks.length).toBe(2);
    expect(varsBlocks[1]).toEqual(varsBlocks[0]);
  });
  it("the consent wording version is not a configured value", () => {
    expect(varsBlocks[0]).not.toContain("CONSENT_WORDING_VERSION");
  });
  it("the two owner dates are still empty (R5 finding 4 is the owner's)", () => {
    for (const k of ["POST_ELECTION_MESSAGE_AT", "DELETION_AT"])
      expect([...cfg.matchAll(new RegExp(`"${k}":\\s*"([^"]*)"`, "g"))].map(m => m[1])).toEqual(["", ""]);
  });
});
