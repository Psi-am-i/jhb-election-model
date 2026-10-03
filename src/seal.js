// Sealed links (owner, 2026-10-03; audits/2026-10-03-share-design/DECISIONS.md).
//
// A shared forecast lives only in its link, so a link alone cannot show when
// it was made: anyone could make one after the result. The site's Worker
// therefore SEALS a link: it signs the link's state (the address keys v, c, f
// and the name n) together with ITS OWN clock's time, with HMAC-SHA256 under
// the Worker secret SEAL_KEY, and the link carries the result as `s`. Anyone
// can ask the Worker to check a link's seal; only the Worker can make one.
//
//   s = <seconds since 1970, base 36> "." <signature, base64url>
//   signed message = "seal1" LF seconds LF v LF c LF f LF n
//
// The name is inside the signature, so a sealed forecast cannot be relabelled
// after the count. Any edit, or a new name, needs a new seal. The Worker
// refuses to seal from the moment polls open (forecast.json
// `election.polls_open`, from cities/<slug>.toml), so only a link sealed before
// then can be eligible for any ranking. Nothing is stored: the Worker keeps no
// record of what it signed, and the seal says nothing about who asked.
//
// Pure apart from crypto.subtle (Workers and node alike). The key is read
// from the environment by the caller and never logged, stored or returned.

export const SEAL_VERSION = "seal1";
export const SEALED_KEYS = ["v", "c", "f", "n"];
const enc = new TextEncoder();

function b64url(bytes) {
  let bin = "";
  for (const b of new Uint8Array(bytes)) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function fromB64url(s) {
  if (!/^[A-Za-z0-9_-]+$/.test(s)) return null;
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4));
  return Uint8Array.from(bin, ch => ch.charCodeAt(0));
}

async function hmacKey(secret, usage) {
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [usage]);
}

// The message a seal signs: the state's four fields, as strings, and the time.
export function sealMessage(fields, seconds) {
  return [SEAL_VERSION, String(seconds), ...SEALED_KEYS.map(k => String(fields[k] ?? ""))].join("\n");
}

// `s` for these fields at `nowMs` (the Worker's clock).
export async function makeSeal(secret, fields, nowMs) {
  const seconds = Math.floor(nowMs / 1000);
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(secret, "sign"), enc.encode(sealMessage(fields, seconds)));
  return seconds.toString(36) + "." + b64url(sig);
}

// { sealed: true, at: ms } when `s` is this Worker's seal of these fields,
// else { sealed: false, at: null }. crypto.subtle.verify compares in constant
// time.
export async function checkSeal(secret, fields, s) {
  const no = { sealed: false, at: null };
  const m = /^([0-9a-z]{1,9})\.([A-Za-z0-9_-]{43})$/.exec(String(s ?? ""));
  if (!m) return no;
  const seconds = parseInt(m[1], 36), sig = fromB64url(m[2]);
  if (!Number.isSafeInteger(seconds) || !sig) return no;
  const ok = await crypto.subtle.verify("HMAC", await hmacKey(secret, "verify"), sig, enc.encode(sealMessage(fields, seconds)));
  return ok ? { sealed: true, at: seconds * 1000 } : no;
}
