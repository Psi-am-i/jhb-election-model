// Validation of a reader's forecast. A forecast is untrusted input.
//
// PURE: no Worker APIs, no bindings, no I/O. The page can import this module and
// run exactly the checks the server runs (one definition, INTEGRATION.md §3d).
//
// Every rule reads generated/forecast.schema.json: the ward list, the roster,
// the model_ref and the share-sum tolerance come from the artefact the schema was
// generated from, never from the request and never from a constant typed here.
//
// A refusal names the field, so a 400 can say which input was wrong.
// The accepted value is REBUILT from the schema (roster order, fresh objects),
// never the caller's object passed through, so nothing the caller attached
// (a `seats` key, a __proto__ key, a getter) survives into storage.

import { BLOCKED_NAME_PATTERNS } from "./blocklist.js";

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
  if (URLISH.test(s)) return refuse("display_name", "may not contain a web address");
  for (const re of BLOCKED_NAME_PATTERNS)
    if (re.test(s)) return refuse("display_name", "not accepted; share as \"A reader\" or choose another name");
  return { ok: true, value: s };
}

export function validateForecast(input, schema) {
  if (!isPlainObject(input)) return refuse("(body)", "must be a JSON object");

  const props = schema.properties;
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

  // combined_share: each party's share of all votes on both ballots, in
  // percent. Keys exactly the roster, finite values in range, summing to 100.
  const cs = input.combined_share;
  if (!isPlainObject(cs)) return refuse("combined_share", "must be an object");
  for (const k of Object.keys(cs))
    if (!roster.includes(k)) return refuse(`combined_share.${k}`, "not a party on the roster");
  const { minimum, maximum } = props.combined_share.properties[roster[0]];
  let sum = 0;
  for (const c of roster) {
    if (!Object.prototype.hasOwnProperty.call(cs, c)) return refuse(`combined_share.${c}`, "required: every party on the roster");
    const v = cs[c];
    if (typeof v !== "number" || !Number.isFinite(v)) return refuse(`combined_share.${c}`, "must be a finite number");
    if (v < minimum || v > maximum) return refuse(`combined_share.${c}`, `must be between ${minimum} and ${maximum}`);
    sum += v;
  }
  const { target, tolerance } = schema["x-share-sum"];
  if (Math.abs(sum - target) > tolerance)
    return refuse("combined_share", `must sum to ${target} (±${tolerance}); sums to ${Math.round(sum * 1000) / 1000}`);

  // coalition: one or more distinct roster parties.
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

  // display_name: only when the reader typed one to show.
  let display_name = null;
  if (input.display_name !== undefined && input.display_name !== null) {
    const n = cleanDisplayName(input.display_name, schema);
    if (!n.ok) return n;
    display_name = n.value;
  }

  return {
    ok: true,
    value: {
      model_ref: input.model_ref,
      ward_calls: wc.slice(),
      combined_share: Object.fromEntries(roster.map(c => [c, cs[c]])),
      coalition: co.slice(),
      mayor,
      display_name,
    },
  };
}
