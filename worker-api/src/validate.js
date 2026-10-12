// Validation of a reader's entry (a prediction, entry version 2). An entry is
// untrusted input.
//
// PURE: no Worker APIs, no bindings, no I/O. The page can import this module and
// run exactly the checks the server runs (one definition, INTEGRATION.md §3d).
//
// Every rule reads the entry schema src/build_make.py writes into
// your-forecast/forecast.json (worker-api/tools/make_schema.mjs build): the
// entry version, the ward list, the roster and the model_ref come from the
// artefact the schema was generated from, never from the request and never
// from a constant typed here.
//
// What is valid is the seat law's refusals (src/reader_seats.py) and the
// shape: whole votes on each ballot for exactly the roster, each ballot
// holding a vote, a ward winner with a ward vote (R1) and, unless it has no
// PR list, a list vote (R2), no list vote for a party with no PR list. The
// editor's bounds (x-editor-bounds) are not validity. An entry of another
// version (version 1 held one combined share) is refused on `v`.
//
// A refusal names the field, so a 400 can say which input was wrong.
// The accepted value is REBUILT from the schema (roster order, fresh objects),
// never the caller's object passed through, so nothing the caller attached
// (a `seats` key, a __proto__ key, a getter) survives into storage.

import { BLOCKED_NAME_PATTERNS } from "./blocklist.js";
import { LABEL_RE } from "../../interactive/js/labels.js";

const refuse = (field, reason) => ({ ok: false, field, reason });

function isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v) &&
    Object.getPrototypeOf(v) === Object.prototype;
}

// Characters that can make a name render as something other than what was
// stored: C0/C1 controls, DEL, zero-width and directional marks, bidi
// embeddings/overrides/isolates, the BOM.
const INVISIBLE = /[\u0000-\u001f\u007f-\u009f​-‏‪-‮⁠-⁤⁦-⁩﻿]/g;
const URLISH = /(https?:|ftp:|mailto:|www\.|:\/\/|\b[a-z0-9-]+\.(com|net|org|co|za|io|ly|me|app|xyz|info|link|site|gov|biz|online|top|shop|tk)\b)/i;

// NAME_MAX_RAW bounds the work done on an input before normalisation: NFKC can
// lengthen a string, so the 40-character limit is applied after it.
const NAME_MAX_RAW = 200;

export function cleanDisplayName(raw, schema) {
  const max = schema.properties.display_name.oneOf[1].maxLength;
  if (typeof raw !== "string") return refuse("display_name", "must be a string or null");
  if (raw.length > NAME_MAX_RAW) return refuse("display_name", `longer than ${max} characters`);
  const s = raw.normalize("NFKC").replace(INVISIBLE, "").replace(/\s+/gu, " ").trim();
  const n = [...s].length;
  if (n === 0) return refuse("display_name", "empty after removing invisible characters");
  if (n > max) return refuse("display_name", `longer than ${max} characters`);
  if (/[<>]/.test(s)) return refuse("display_name", "may not contain < or >");
  // A typed label may not take the shape of a random default ("pollster-23"):
  // it could copy another reader's label. A reader who wants their own
  // default back sends null.
  if (LABEL_RE.test(s.toLowerCase())) return refuse("display_name", "that shape is kept for random labels; leave the label empty to use yours");
  // Owner, 2026-09-29: a label is never an email address (nor derived from one).
  if (/[^\s@]+@[^\s@]+\.[^\s@]+/.test(s)) return refuse("display_name", "may not contain an email address");
  if (URLISH.test(s)) return refuse("display_name", "may not contain a web address");
  for (const re of BLOCKED_NAME_PATTERNS)
    if (re.test(s)) return refuse("display_name", "not accepted; share as \"A reader\" or choose another name");
  return { ok: true, value: s };
}

export function validateForecast(input, schema) {
  if (!isPlainObject(input)) return refuse("(body)", "must be a JSON object");

  const props = schema.properties;
  // The version first: a body of another version is named as one, whatever
  // else it carries.
  if (input.v !== props.v.const) return refuse("v", "made by another version of this page");
  for (const k of Object.keys(input))
    if (!Object.prototype.hasOwnProperty.call(props, k))
      return refuse(k, "not accepted" + (k === "seats" ? " (seats are computed on the server from the calls)" : ""));
  for (const k of schema.required)
    if (!(k in input)) return refuse(k, "required");

  // model_ref: a published run's artefact key.
  if (!props.model_ref.enum.includes(input.model_ref))
    return refuse("model_ref", "not a published run");

  const roster = props.ward_calls.items.enum;
  const inRoster = c => typeof c === "string" && roster.includes(c);

  // ward_calls: exactly one roster code per ward, in ward order.
  const wc = input.ward_calls;
  const nWards = props.ward_calls.minItems;
  if (!Array.isArray(wc)) return refuse("ward_calls", "must be an array");
  if (wc.length !== nWards) return refuse("ward_calls", `must have exactly ${nWards} entries, one per ward`);
  for (let i = 0; i < wc.length; i++)
    if (!inRoster(wc[i])) return refuse(`ward_calls[${i}]`, "not a party on the roster");

  // ward_votes, list_votes: each party's whole votes on that ballot. Keys
  // exactly the roster, safe non-negative integers, each ballot holding a vote.
  const noList = new Set(schema["x-seat-context"].no_pr_list);
  const ballots = {};
  for (const name of ["ward_votes", "list_votes"]) {
    const m = input[name];
    if (!isPlainObject(m)) return refuse(name, "must be an object");
    for (const k of Object.keys(m))
      if (!roster.includes(k)) return refuse(`${name}.${k}`, "not a party on the roster");
    let sum = 0;
    for (const c of roster) {
      if (!Object.prototype.hasOwnProperty.call(m, c)) return refuse(`${name}.${c}`, "required: every party on the roster");
      const v = m[c];
      if (!Number.isSafeInteger(v) || v < 0) return refuse(`${name}.${c}`, "must be a whole number of votes, 0 or more");
      sum += v;
    }
    if (!(sum >= 1)) return refuse(name, "must hold at least one vote");
    ballots[name] = m;
  }
  for (const c of noList)
    if (ballots.list_votes[c] > 0) return refuse(`list_votes.${c}`, "this party has no PR list");
  // R1 and R2 (src/reader_seats.py): a ward winner has a ward vote, and a list
  // vote unless it has no PR list.
  for (const c of new Set(wc)) {
    if (!(ballots.ward_votes[c] > 0)) return refuse(`ward_votes.${c}`, "wins a ward, so it needs a ward vote");
    if (!noList.has(c) && !(ballots.list_votes[c] > 0)) return refuse(`list_votes.${c}`, "wins a ward, so it needs a list vote");
  }

  // coalition: distinct roster parties, none or more.
  const co = input.coalition;
  if (!Array.isArray(co)) return refuse("coalition", "must be an array");
  if (co.length < props.coalition.minItems) return refuse("coalition", "must name at least one party");
  for (let i = 0; i < co.length; i++)
    if (!inRoster(co[i])) return refuse(`coalition[${i}]`, "not a party on the roster");
  if (new Set(co).size !== co.length) return refuse("coalition", "a party is listed twice");

  // mayor: absent, null, or a member of the coalition.
  const mayor = input.mayor ?? null;
  if (mayor !== null) {
    if (!inRoster(mayor)) return refuse("mayor", "not a party on the roster");
    if (!co.includes(mayor)) return refuse("mayor", "must be a member of the coalition");
  }

  // display_name: the forecast's LABEL, when the reader chose one (their own
  // text, or their X @username kept as the default). null means "show this
  // forecast's random default label" (interactive/js/labels.js), which the
  // server assigns; no real name is ever collected.
  let display_name = null;
  if (input.display_name !== undefined && input.display_name !== null) {
    const n = cleanDisplayName(input.display_name, schema);
    if (!n.ok) return n;
    display_name = n.value;
  }

  return {
    ok: true,
    value: {
      v: input.v,
      model_ref: input.model_ref,
      ward_calls: wc.slice(),
      ward_votes: Object.fromEntries(roster.map(c => [c, ballots.ward_votes[c]])),
      list_votes: Object.fromEntries(roster.map(c => [c, ballots.list_votes[c]])),
      coalition: co.slice(),
      mayor,
      display_name,
    },
  };
}
