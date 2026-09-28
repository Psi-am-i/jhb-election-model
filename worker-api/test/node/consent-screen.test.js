// The consent screen (interactive/js/auth-ui.js) against the server's contract
// (src/consent.js), the wording version, the default labels, and the draft
// privacy notice. R5 findings 5, 6 and 8; owner decisions of 2026-09-29.
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { consentTerms, consentPayload, wordingVersion, canonicalText, deletionDateText, CONSENT_KEYS,
  SCREEN_PURPOSES, PROVIDER_LABELS, DATE_NOT_SET } from "../../../interactive/js/consent-terms.js";
import { consentScreenHTML, PROVIDERS as PAGE_PROVIDERS } from "../../../interactive/js/auth-ui.js";
import { LABEL_WORDS, LABEL_MAX_NUMBER, LABEL_RE, randomLabel, randomBelow, handleLabel } from "../../../interactive/js/labels.js";
import { cleanDisplayName } from "../../src/validate.js";
import { BLOCKED_NAME_PATTERNS } from "../../src/blocklist.js";
import schema from "../../generated/forecast.schema.json" with { type: "json" };

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const repo = resolve(root, "..");
const text = html => html.replace(/<[^>]+>/g, " ").replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/×/g, " ").replace(/\s+/g, " ").trim();

describe("the page sends exactly the keys the server accepts (R5 finding 6)", () => {
  const serverProviders = [...readFileSync(resolve(root, "src/providers.js"), "utf8").matchAll(/^  (\w+): \{$/gm)].map(m => m[1]);

  it("the payload the page builds has only CONSENT_KEYS, and every purpose as a boolean", () => {
    const p = consentPayload({ store: true, age18: true, contact_if_win: false, updates: true, contact: " a@example.com ", wording_version: "w1-x" });
    expect(Object.keys(p).sort()).toEqual([...CONSENT_KEYS].sort());
    for (const k of SCREEN_PURPOSES) expect(typeof p[k]).toBe("boolean");
    expect(p.contact).toBe("a@example.com");
    expect("contact" in consentPayload({ store: true, age18: true, wording_version: "w" })).toBe(false);
  });
  it("the old page's keys are not among them (show_name, display_name, email)", () => {
    for (const k of ["show_name", "display_name", "email"]) expect(CONSENT_KEYS).not.toContain(k);
  });
  it("the server's consent module takes its purposes and keys from the same file", () => {
    const src = readFileSync(resolve(root, "src/consent.js"), "utf8");
    expect(src).toMatch(/from "\.\.\/\.\.\/interactive\/js\/consent-terms\.js"/);
    expect(src).not.toMatch(/SCREEN_PURPOSES = \[/);
  });
  it("the page offers the server's providers, Microsoft included, and no magic link", () => {
    expect([...PAGE_PROVIDERS].sort()).toEqual([...serverProviders].sort());
    expect(PAGE_PROVIDERS).toContain("microsoft");
    for (const p of PAGE_PROVIDERS) expect(PROVIDER_LABELS[p]).toBeTruthy();
    const ui = readFileSync(resolve(repo, "interactive/js/auth-ui.js"), "utf8");
    const stub = readFileSync(resolve(repo, "interactive/js/api-stub.js"), "utf8");
    for (const t of [ui, stub]) expect(t).not.toMatch(/sign-in link|magic|\/auth\/email/i);
  });
});

describe("the wording version is a hash of the displayed text (R5 finding 6)", () => {
  const terms = consentTerms({ deletionDate: DATE_NOT_SET });

  it("is stable for the same text and changes with any one string", async () => {
    const v = await wordingVersion(terms);
    expect(v).toMatch(/^w1-[0-9a-f]{24}$/);
    expect(await wordingVersion(consentTerms({ deletionDate: DATE_NOT_SET }))).toBe(v);
    const edited = structuredClone(terms); edited.boxes.age18 += " ";
    expect(await wordingVersion(edited)).not.toBe(v);
    const edited2 = structuredClone(terms); edited2.facts[3][1] = edited2.facts[3][1].replace("score", "rate");
    expect(await wordingVersion(edited2)).not.toBe(v);
  });
  it("the deletion date is part of the displayed text, so part of the hash", async () => {
    const set = consentTerms({ deletionDate: deletionDateText("2027-01-31T09:00:00+02:00") });
    expect(canonicalText(set)).toMatch(/2027-01-31/);
    expect(await wordingVersion(set)).not.toBe(await wordingVersion(terms));
  });

  // Every word the screen shows is in the hashed terms, apart from the
  // provider's name. A string typed into auth-ui.js outside the terms would be
  // shown but not hashed; this finds it.
  for (const s of [
    { provider: "google", contact_confirmed: true },
    { provider: "facebook", contact_confirmed: false, unconfirmed_contact: "a@example.com" },
  ]) {
    it(`nothing is shown that is not hashed (${s.provider})`, () => {
      let shown = text(consentScreenHTML(s, terms));
      const strings = [terms.title, terms.signedInWith, terms.requiredHeading, terms.optionalHeading,
        terms.contactLabel, terms.contactHelp, terms.submit, terms.cancel,
        ...Object.values(terms.boxes), ...Object.values(terms.links), ...terms.facts.flat()]
        .sort((a, b) => b.length - a.length);
      expect(shown.length).toBeGreaterThan(500);
      for (const t of strings) shown = shown.split(t.replace(/\s+/g, " ")).join(" ");
      shown = shown.split(PROVIDER_LABELS[s.provider]).join(" ");
      expect(shown.replace(/[\s.·]/g, "")).toBe("");
    });
  }
  it("the detector can see: a stray sentence on the screen is left over", () => {
    let shown = text(consentScreenHTML({ provider: "x", contact_confirmed: false }, terms).replace("</form>", "<p>We may share your data.</p></form>"));
    for (const t of [terms.title, terms.signedInWith, terms.requiredHeading, terms.optionalHeading, terms.contactLabel,
      terms.contactHelp, terms.submit, terms.cancel, ...Object.values(terms.boxes), ...Object.values(terms.links), ...terms.facts.flat()])
      shown = shown.split(t.replace(/\s+/g, " ")).join(" ");
    expect(shown.replace(/[\s.·X]/g, "")).toMatch(/Wemayshareyourdata/);
  });
});

describe("the consent wording says what the code does (R5 finding 5)", () => {
  const all = canonicalText(consentTerms({ deletionDate: DATE_NOT_SET }));
  it("states the one post-election email, sent whatever is ticked", () => {
    expect(all).toMatch(/Whatever you tick here, we send one email after the election/);
  });
  it("states that anyone with the link can see a prediction", () => expect(all).toMatch(/Anyone with the link/));
  it("states that saved predictions are analysed against past elections", () =>
    expect(all).toMatch(/analyse saved predictions against the result and against past elections/));
  it("states what happens without a confirmed email (finding 2)", () =>
    expect(all).toMatch(/If we hold no confirmed address for you, we cannot send that email/));
  it("does not claim an email is needed to delete; says the opposite", () => {
    expect(all).not.toMatch(/need (one|an email) to let you delete/i);
    expect(all).toMatch(/You do not need an email address to delete/);
  });
  it("states the copies that outlive a deletion (finding 8)", () =>
    expect(all).toMatch(/database backups up to 30 days, service logs up to 7 days/));
  it("frames the forecast as a prediction and collects no name (owner, 2026-09-29)", () => {
    expect(all).not.toMatch(/political (views|persuasion)/i);
    expect(all).toMatch(/We do not collect your name/);
  });
});

describe("default labels (owner, 2026-09-29)", () => {
  const roster = schema["x-parties"];

  it("every word is lower-case letters and passes the display-name validator (blocklist, URL, markup)", () => {
    expect(LABEL_WORDS.length).toBeGreaterThanOrEqual(10);
    expect(new Set(LABEL_WORDS).size).toBe(LABEL_WORDS.length);
    for (const w of LABEL_WORDS) {
      expect(w).toMatch(/^[a-z]+$/);
      expect(cleanDisplayName(w, schema).ok, w).toBe(true);
    }
  });
  it("a TYPED label in the random shape is refused, so no reader can copy another's label", () => {
    for (const l of ["pollster-23", "Pollster-23", `${LABEL_WORDS.at(-1)}-${LABEL_MAX_NUMBER}`]) {
      const r = cleanDisplayName(l, schema);
      expect(r.ok, l).toBe(false);
      expect(r.reason).toMatch(/random labels/);
    }
    expect(cleanDisplayName("pollster 23", schema).ok).toBe(true);
    expect(cleanDisplayName("pollster-0", schema).ok).toBe(true);
  });
  it("no word hits the blocklist, an official-sounding word, or a party name or code", () => {
    const official = /iec|official|admin|moderator|staff|electoral|commission|government|mayor/;
    for (const w of LABEL_WORDS) {
      for (const re of BLOCKED_NAME_PATTERNS) expect(re.test(w), `${w} vs ${re}`).toBe(false);
      expect(w).not.toMatch(official);
      for (const p of roster) {
        expect(w.includes(p.code.toLowerCase()) && p.code.length >= 3, `${w} contains ${p.code}`).toBe(false);
        expect(w).not.toBe(p.name.toLowerCase().replace(/[^a-z]/g, ""));
      }
    }
  });
  it("the party check can see: a party code as a word is caught", () => {
    const code = roster.find(p => p.code.length >= 3).code.toLowerCase();
    expect(`${code}fan`.includes(code)).toBe(true);
  });
  it("labels match the pattern, spread over every word and the whole number range", () => {
    const n = 40000, words = new Map(), nums = [];
    for (let i = 0; i < n; i++) {
      const l = randomLabel();
      const m = LABEL_RE.exec(l);
      expect(m, l).not.toBe(null);
      words.set(m[1], (words.get(m[1]) || 0) + 1);
      nums.push(Number(m[2]));
    }
    expect(words.size).toBe(LABEL_WORDS.length);
    const expected = n / LABEL_WORDS.length;
    for (const [w, c] of words) expect(Math.abs(c - expected) / expected, w).toBeLessThan(0.15);
    expect(Math.min(...nums)).toBeGreaterThanOrEqual(1);
    expect(Math.max(...nums)).toBeLessThanOrEqual(LABEL_MAX_NUMBER);
    expect(nums.filter(x => x > LABEL_MAX_NUMBER / 2).length / n).toBeGreaterThan(0.45);
    expect(nums.filter(x => x > LABEL_MAX_NUMBER / 2).length / n).toBeLessThan(0.55);
  });
  it("randomBelow discards the incomplete top range instead of folding it (no modulo bias)", () => {
    // n = 3: 2^32 is not a multiple of 3, so the top value must be rejected.
    const seq = [2 ** 32 - 1, 7];
    const rand = a => { a[0] = seq.shift(); return a; };
    expect(randomBelow(3, rand)).toBe(7 % 3);
    expect(seq.length).toBe(0);
  });
  it("an X username becomes @username; anything else is not used", () => {
    expect(handleLabel("reader_x")).toBe("@reader_x");
    for (const bad of [null, "", "a".repeat(16), "has space", "x@y.com", "<b>"]) expect(handleLabel(bad)).toBe(null);
    expect(cleanDisplayName("@reader_x", schema).ok).toBe(true);
  });
  it("a label that is an email address is refused", () => {
    for (const e of ["reader@example.fr", "me: a.b@c.de"]) {
      const r = cleanDisplayName(e, schema);
      expect(r.ok, e).toBe(false);
      expect(r.reason).toMatch(/email/);
    }
  });
});

describe("the draft privacy notice (R5 findings 3, 4, 8: text for the owner and counsel)", () => {
  const html = readFileSync(resolve(repo, "interactive/privacy-placeholder.html"), "utf8");
  const t = text(html);
  it("is marked as a draft, with placeholders for the owner's decisions", () => {
    expect(t).toMatch(/DRAFT/);
    for (const ph of ["[Responsible party", "[Information Officer", "[Where the data is stored", "[Post-election message date", "[Deletion date"])
      expect(t, ph).toContain(ph);
  });
  it("names every processor", () => {
    for (const p of ["Google", "Apple", "Microsoft", "Meta", "X Corp", "Cloudflare Workers", "Cloudflare D1", "Cloudflare R2",
      "Workers Logs", "Turnstile", "Cloudflare Email Service"]) expect(t, p).toContain(p);
  });
  it("states each retention window, and marks the ones not confirmed", () => {
    expect(t).toMatch(/Time Travel[^.]*30 days/);
    expect(t).toMatch(/Workers Logs[^.]*7 days/);
    expect(t).toMatch(/one year/);
    expect(t).toMatch(/\[unconfirmed/i);
  });
  it("states the owner's positions for counsel to confirm", () => {
    expect(t).toMatch(/forecast of how the election will turn out, not a statement of how you vote/);
    expect(t).toMatch(/ordinary personal information, not special personal information[^[]*\[counsel to confirm\]/);
    expect(t).toMatch(/We do not collect your name/);
    expect(t).toMatch(/section 72/);
  });
});
