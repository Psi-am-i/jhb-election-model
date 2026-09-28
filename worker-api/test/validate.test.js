// Each refusal is tested with a CONSTRUCTED violation of an otherwise valid
// forecast, and the same forecast without the violation is accepted, so a
// refusal is caused by the violation and nothing else.
import { describe, it, expect } from "vitest";
import { validateForecast, cleanDisplayName } from "../src/validate.js";
import { schema, roster, nWards, validForecast, clone } from "./helpers.js";

const v = f => validateForecast(f, schema);
const last = roster[roster.length - 1];

// [what, mutate(forecast) -> forecast, field the refusal must name]
const REFUSALS = [
  ["body is an array", () => [], "(body)"],
  ["body is null", () => null, "(body)"],
  ["body is a string", () => "forecast", "(body)"],
  ["client sends seats", f => ({ ...f, seats: { [roster[0]]: 270 } }), "seats"],
  ["client sends an id", f => ({ ...f, id: "abcdefghij" }), "id"],
  ["__proto__ key", f => JSON.parse(JSON.stringify(f).replace(/^\{/, '{"__proto__":{"x":1},')), "__proto__"],
  ["model_ref missing", f => { delete f.model_ref; return f; }, "model_ref"],
  ["ward_calls missing", f => { delete f.ward_calls; return f; }, "ward_calls"],
  ["combined_share missing", f => { delete f.combined_share; return f; }, "combined_share"],
  ["coalition missing", f => { delete f.coalition; return f; }, "coalition"],
  ["model_ref not published", f => ({ ...f, model_ref: "not-a-run" }), "model_ref"],
  ["ward_calls not an array", f => ({ ...f, ward_calls: {} }), "ward_calls"],
  ["one ward short", f => ({ ...f, ward_calls: f.ward_calls.slice(1) }), "ward_calls"],
  ["one ward too many", f => ({ ...f, ward_calls: [...f.ward_calls, roster[0]] }), "ward_calls"],
  ["ward call off the roster", f => { f.ward_calls[7] = "NOPE"; return f; }, "ward_calls[7]"],
  ["ward call empty", f => { f.ward_calls[0] = ""; return f; }, "ward_calls[0]"],
  ["ward call null (uncalled ward)", f => { f.ward_calls[nWards - 1] = null; return f; }, `ward_calls[${nWards - 1}]`],
  ["ward call a number", f => { f.ward_calls[3] = 1; return f; }, "ward_calls[3]"],
  ["combined_share an array", f => ({ ...f, combined_share: [] }), "combined_share"],
  ["combined_share party missing", f => { delete f.combined_share[last]; return f; }, `combined_share.${last}`],
  ["combined_share extra party", f => { f.combined_share.NOPE = 0; return f; }, "combined_share.NOPE"],
  ["combined_share a string", f => { f.combined_share[last] = "5"; return f; }, `combined_share.${last}`],
  ["combined_share NaN", f => { f.combined_share[last] = NaN; return f; }, `combined_share.${last}`],
  ["combined_share Infinity", f => { f.combined_share[last] = Infinity; return f; }, `combined_share.${last}`],
  ["combined_share negative", f => { f.combined_share[roster[0]] += f.combined_share[last] + 1; f.combined_share[last] = -1; return f; }, `combined_share.${last}`],
  ["combined_share over 100", f => { f.combined_share[last] = 101; return f; }, `combined_share.${last}`],
  ["combined_share sums to 100.6", f => { f.combined_share[roster[0]] += 0.6; return f; }, "combined_share"],
  ["combined_share sums to 99.4", f => { f.combined_share[roster[0]] -= 0.6; return f; }, "combined_share"],
  ["coalition not an array", f => ({ ...f, coalition: roster[0] }), "coalition"],
  ["coalition empty", f => ({ ...f, coalition: [], mayor: null }), "coalition"],
  ["coalition off the roster", f => ({ ...f, coalition: [roster[0], "NOPE"] }), "coalition[1]"],
  ["coalition duplicate", f => ({ ...f, coalition: [roster[0], roster[0]] }), "coalition"],
  ["mayor off the roster", f => ({ ...f, mayor: "NOPE" }), "mayor"],
  ["mayor outside the coalition", f => ({ ...f, mayor: last }), "mayor"],
  ["display_name a number", f => ({ ...f, display_name: 7 }), "display_name"],
  ["display_name empty", f => ({ ...f, display_name: "" }), "display_name"],
  ["display_name only invisible", f => ({ ...f, display_name: "​‮⁦" }), "display_name"],
  ["display_name 41 chars", f => ({ ...f, display_name: "a".repeat(41) }), "display_name"],
  ["display_name 201 raw chars", f => ({ ...f, display_name: " ".repeat(201) + "a" }), "display_name"],
  ["display_name a URL", f => ({ ...f, display_name: "see https://x.io" }), "display_name"],
  ["display_name www", f => ({ ...f, display_name: "www.example" }), "display_name"],
  ["display_name a domain", f => ({ ...f, display_name: "vote.co.za" }), "display_name"],
  ["display_name markup", f => ({ ...f, display_name: "<b>x</b>" }), "display_name"],
  ["display_name blocklisted", f => ({ ...f, display_name: "The Model" }), "display_name"],
];

describe("validateForecast refusals", () => {
  it("the base fixture is valid", () => {
    const r = v(validForecast());
    expect(r.ok, JSON.stringify(r)).toBe(true);
  });

  for (const [what, mutate, field] of REFUSALS) {
    it(`refuses: ${what}`, () => {
      const base = validForecast();
      expect(v(clone(base)).ok).toBe(true);            // valid without the violation
      const r = v(mutate(clone(base)));
      expect(r.ok).toBe(false);
      expect(r.field).toBe(field);
      expect(v(clone(base)).ok).toBe(true);            // and quiet again once reverted
    });
  }

  it("every schema property has at least one refusal case (population check)", () => {
    const covered = new Set(REFUSALS.map(([, , f]) => f.replace(/[.[].*$/, "")));
    for (const p of Object.keys(schema.properties)) expect(covered, p).toContain(p);
  });
});

describe("validateForecast acceptances", () => {
  it("accepts PR shares inside the tolerance", () => {
    const f = validForecast(); f.combined_share[roster[0]] += 0.4;
    expect(v(f).ok).toBe(true);
  });
  it("accepts a null mayor and no display name", () => {
    const f = validForecast(); f.mayor = null; delete f.display_name;
    const r = v(f);
    expect(r.ok).toBe(true);
    expect(r.value.display_name).toBe(null);
  });
  it("rebuilds the value: combined_share in roster order, no caller-attached keys", () => {
    const f = validForecast();
    f.combined_share = Object.fromEntries(Object.entries(f.combined_share).reverse());
    const r = v(f);
    expect(Object.keys(r.value.combined_share)).toEqual(roster);
    expect(Object.keys(r.value).sort()).toEqual(["coalition", "combined_share", "display_name", "mayor", "model_ref", "ward_calls"]);
  });
});

describe("cleanDisplayName", () => {
  it("strips bidi overrides and zero-width characters", () => {
    expect(cleanDisplayName("Th‮andi​ M.", schema)).toEqual({ ok: true, value: "Thandi M." });
  });
  it("NFKC-normalises full-width letters", () => {
    expect(cleanDisplayName("Ｔｈａｎｄｉ", schema).value).toBe("Thandi");
  });
  it("collapses whitespace", () => {
    expect(cleanDisplayName("  A   reader \n ", schema).value).toBe("A reader");
  });
  it("counts the 40-character limit in code points", () => {
    expect(cleanDisplayName("😀".repeat(40), schema).ok).toBe(true);
    expect(cleanDisplayName("😀".repeat(41), schema).ok).toBe(false);
  });
});

describe("the schema scanned the right population", () => {
  it("has one ward entry per ward seat and one roster entry per party", () => {
    expect(schema["x-ward-ids"].length).toBe(schema["x-council"].ward_seats);
    expect(nWards).toBe(schema["x-council"].ward_seats);
    expect(roster).toEqual(schema["x-parties"].map(p => p.code));
    expect(Object.keys(schema.properties.combined_share.properties)).toEqual(roster);
  });
});
