// Each refusal is tested with a CONSTRUCTED violation of an otherwise valid
// entry (version 2: whole votes on the ward and list ballots), and the same
// entry without the violation is accepted, so a refusal is caused by the
// violation and nothing else.
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
  ["v missing", f => { delete f.v; return f; }, "v"],
  ["v of another version", f => ({ ...f, v: "1" }), "v"],
  // guard G12: a version 1 body (one combined share) is refused on its version
  ["a version 1 body", f => { const { ward_votes, list_votes, ...rest } = f;
    return { ...rest, v: "1", combined_share: Object.fromEntries(roster.map(c => [c, 100 / roster.length])) }; }, "v"],
  ["model_ref missing", f => { delete f.model_ref; return f; }, "model_ref"],
  ["ward_calls missing", f => { delete f.ward_calls; return f; }, "ward_calls"],
  ["ward_votes missing", f => { delete f.ward_votes; return f; }, "ward_votes"],
  ["list_votes missing", f => { delete f.list_votes; return f; }, "list_votes"],
  ["coalition missing", f => { delete f.coalition; return f; }, "coalition"],
  ["model_ref not published", f => ({ ...f, model_ref: "not-a-run" }), "model_ref"],
  ["ward_calls not an array", f => ({ ...f, ward_calls: {} }), "ward_calls"],
  ["one ward short", f => ({ ...f, ward_calls: f.ward_calls.slice(1) }), "ward_calls"],
  ["one ward too many", f => ({ ...f, ward_calls: [...f.ward_calls, roster[0]] }), "ward_calls"],
  ["ward call off the roster", f => { f.ward_calls[7] = "NOPE"; return f; }, "ward_calls[7]"],
  ["ward call empty", f => { f.ward_calls[0] = ""; return f; }, "ward_calls[0]"],
  ["ward call null (uncalled ward)", f => { f.ward_calls[nWards - 1] = null; return f; }, `ward_calls[${nWards - 1}]`],
  ["ward call a number", f => { f.ward_calls[3] = 1; return f; }, "ward_calls[3]"],
  ...["ward_votes", "list_votes"].flatMap(b => [
    [`${b} an array`, f => ({ ...f, [b]: [] }), b],
    [`${b} party missing`, f => { delete f[b][last]; return f; }, `${b}.${last}`],
    [`${b} extra party`, f => { f[b].NOPE = 0; return f; }, `${b}.NOPE`],
    [`${b} a string`, f => { f[b][last] = "5"; return f; }, `${b}.${last}`],
    [`${b} a fraction`, f => { f[b][last] = 5.5; return f; }, `${b}.${last}`],
    [`${b} NaN`, f => { f[b][last] = NaN; return f; }, `${b}.${last}`],
    [`${b} negative`, f => { f[b][last] = -1; return f; }, `${b}.${last}`],
    [`${b} past a safe integer`, f => { f[b][last] = 2 ** 53; return f; }, `${b}.${last}`],
  ]),
  // R1 and R2: a ward winner with no ward vote, or no list vote
  ["R1: a ward winner with no ward vote", f => { f.ward_votes[roster[0]] = 0; return f; }, `ward_votes.${roster[0]}`],
  ["R2: a ward winner with no list vote", f => { f.list_votes[roster[0]] = 0; return f; }, `list_votes.${roster[0]}`],
  ["a ballot with no vote", f => { for (const c of roster) f.list_votes[c] = 0; return f; }, "list_votes"],
  ["coalition not an array", f => ({ ...f, coalition: roster[0] }), "coalition"],
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
  it("accepts any ballot totals: each ballot's total is the sum of its votes", () => {
    const f = validForecast(); f.list_votes[roster[0]] += 123456;
    expect(v(f).ok).toBe(true);
  });
  it("accepts a party that wins no ward with no vote on either ballot", () => {
    const f = validForecast(); f.ward_calls = f.ward_calls.map(c => (c === last ? roster[0] : c));
    f.ward_votes[last] = 0; f.list_votes[last] = 0;
    expect(v(f).ok).toBe(true);
  });
  it("accepts no coalition: who governs is optional and not scored", () => {
    const f = validForecast(); f.coalition = []; f.mayor = null;
    expect(v(f).ok).toBe(true);
  });
  it("accepts a null mayor and no display name", () => {
    const f = validForecast(); f.mayor = null; delete f.display_name;
    const r = v(f);
    expect(r.ok).toBe(true);
    expect(r.value.display_name).toBe(null);
  });
  it("rebuilds the value: both ballots in roster order, no caller-attached keys", () => {
    const f = validForecast();
    f.ward_votes = Object.fromEntries(Object.entries(f.ward_votes).reverse());
    f.list_votes = Object.fromEntries(Object.entries(f.list_votes).reverse());
    const r = v(f);
    expect(Object.keys(r.value.ward_votes)).toEqual(roster);
    expect(Object.keys(r.value.list_votes)).toEqual(roster);
    expect(Object.keys(r.value).sort()).toEqual(["coalition", "display_name", "list_votes", "mayor", "model_ref", "v", "ward_calls", "ward_votes"]);
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
    expect(Object.keys(schema.properties.ward_votes.properties)).toEqual(roster);
    expect(Object.keys(schema.properties.list_votes.properties)).toEqual(roster);
  });
});
