// Random ids, hashing, and HMAC-signed tokens. Web Crypto only.

const B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

// Unbiased base62: bytes >= 248 (= 4 * 62) are discarded rather than folded.
export function randomId(n = 10) {
  let out = "";
  while (out.length < n) {
    for (const b of crypto.getRandomValues(new Uint8Array(n * 2))) {
      if (b < 248) out += B62[b % 62];
      if (out.length === n) break;
    }
  }
  return out;
}

export function b64url(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(str) {
  const s = str.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "===".slice((s.length + 3) % 4));
  return Uint8Array.from(bin, c => c.charCodeAt(0));
}

const enc = new TextEncoder();

export async function sha256Hex(text) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  return Array.from(d, b => b.toString(16).padStart(2, "0")).join("");
}

async function hmacKey(secret) {
  if (!secret) throw new Error("SESSION_SIGNING_KEY is not set");
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

// A signed token: base64url(JSON payload) "." base64url(HMAC). `purpose` is
// bound into the MAC so a token minted for one use cannot be replayed at
// another endpoint. `exp` is seconds since the epoch.
export async function signToken(secret, purpose, payload, ttlSeconds, now = Date.now()) {
  const body = b64url(enc.encode(JSON.stringify({ ...payload, _p: purpose, exp: Math.floor(now / 1000) + ttlSeconds })));
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret), enc.encode(purpose + "." + body)));
  return body + "." + b64url(mac);
}

// Returns the payload, or null for any failure (bad shape, bad MAC, wrong
// purpose, expired). crypto.subtle.verify compares in constant time.
export async function verifyToken(secret, purpose, token, now = Date.now()) {
  if (typeof token !== "string" || token.length > 4096) return null;
  const [body, mac, extra] = token.split(".");
  if (!body || !mac || extra !== undefined) return null;
  let ok = false;
  try {
    ok = await crypto.subtle.verify("HMAC", await hmacKey(secret), b64urlDecode(mac), enc.encode(purpose + "." + body));
  } catch { return null; }
  if (!ok) return null;
  let p;
  try { p = JSON.parse(new TextDecoder().decode(b64urlDecode(body))); } catch { return null; }
  if (p._p !== purpose || typeof p.exp !== "number" || p.exp * 1000 <= now) return null;
  return p;
}

// Constant-time equality for two short strings (OAuth state).
export async function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const [ha, hb] = await Promise.all([sha256Hex(a), sha256Hex(b)]);
  let d = 0;
  for (let i = 0; i < ha.length; i++) d |= ha.charCodeAt(i) ^ hb.charCodeAt(i);
  return d === 0;
}
