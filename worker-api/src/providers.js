// Sign-in providers (owner, DESIGN-decided §9): Google, Apple, Facebook, X,
// Microsoft. Built on `arctic` (v3), which runs on Workers.
//
// Instagram is not a provider: Meta closed Instagram personal-account sign-in
// (the Basic Display API) in December 2024. Facebook Login covers Meta users.
//
// WHAT IS TAKEN from each provider: the stable account id (`sub`) and, when the
// provider gives one, an email (or a phone number) as the single contact route.
// Nothing else is requested: no name, photo, friends, location. Scopes are the
// minimum that yields those two things.
//
// PKCE (S256) is used where arctic exposes it: Google, X, Microsoft. arctic's
// Apple and Facebook clients take no code verifier; those two flows are bound
// by `state` (and Apple's by an id_token `nonce` too).
//
// ID TOKENS (Google, Apple, Microsoft) are decoded with arctic's decodeIdToken,
// which does NOT check the signature. That is permitted here because each token
// is received directly from the provider's token endpoint over TLS in the
// back-channel code exchange, authenticated with our client secret (OpenID
// Connect Core 1.0 §3.1.3.7, item 6). It is never accepted from the browser.
// The claims are still checked: iss, aud, exp, and nonce (checkIdToken).

import { Google, Apple, Facebook, Twitter, MicrosoftEntraId, decodeIdToken } from "arctic";
import { HttpError } from "./http.js";
import { handleLabel } from "../../interactive/js/labels.js";

const callback = (env, p) => `${env.SITE_ORIGIN}/auth/${p}/callback`;

function need(env, ...names) {
  // Unconfigured provider: 503, and the secret's NAME only goes to the log.
  for (const n of names) if (!env[n]) {
    console.error(JSON.stringify({ msg: "sign-in provider not configured", missing: n }));
    throw new HttpError(503, "this sign-in option is not available yet");
  }
}

// Apple's private key arrives as the .p8 file's PEM text (a secret). arctic
// wants the PKCS#8 DER bytes.
export function pemToPkcs8(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PRIVATE KEY-----/g, "").replace(/\s+/g, "");
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

// Claims of an id_token received from a token endpoint (see header).
export function checkIdToken(claims, { iss, aud, nonce, now = Date.now() }) {
  const issOk = typeof iss === "function" ? iss(claims.iss, claims) : [].concat(iss).includes(claims.iss);
  if (!issOk) throw new Error("id_token: wrong issuer");
  const auds = [].concat(claims.aud);
  if (!auds.includes(aud)) throw new Error("id_token: wrong audience");
  if (typeof claims.exp !== "number" || claims.exp * 1000 <= now) throw new Error("id_token: expired");
  if (nonce !== undefined && claims.nonce !== nonce) throw new Error("id_token: nonce mismatch");
  if (typeof claims.sub !== "string" || !claims.sub) throw new Error("id_token: no subject");
  return claims;
}

const truthy = v => v === true || v === "true";

async function hmacHex(key, msg) {
  const enc = new TextEncoder();
  const k = await crypto.subtle.importKey("raw", enc.encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const s = new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(msg)));
  return Array.from(s, b => b.toString(16).padStart(2, "0")).join("");
}

async function getJson(url, headers) {
  const r = await fetch(url, { headers });
  if (!r.ok) throw new Error(`provider API ${new URL(url).host} answered ${r.status}`);
  return r.json();
}

// Each provider: pkce, the HTTP method its callback arrives by, the SameSite
// the state cookie needs to survive that callback, authorizationURL(), identity().
// identity() returns { sub, contact_kind, contact, contact_verified } and, for X
// only, `handle` (the username). No provider's name is ever read.
export const PROVIDERS = {
  google: {
    pkce: true, callbackMethod: "GET", sameSite: "Lax",
    client(env) {
      need(env, "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET");
      return new Google(env.GOOGLE_CLIENT_ID, env.GOOGLE_CLIENT_SECRET, callback(env, "google"));
    },
    authorizationURL(env, { state, verifier, nonce }) {
      const u = this.client(env).createAuthorizationURL(state, verifier, ["openid", "email"]);
      u.searchParams.set("nonce", nonce);
      return u;
    },
    async identity(env, { code, verifier, nonce }) {
      const tokens = await this.client(env).validateAuthorizationCode(code, verifier);
      const c = checkIdToken(decodeIdToken(tokens.idToken()), {
        iss: ["https://accounts.google.com", "accounts.google.com"], aud: env.GOOGLE_CLIENT_ID, nonce });
      return contactFromEmail(c.sub, c.email, truthy(c.email_verified));
    },
  },

  apple: {
    // Apple posts the callback (response_mode=form_post), cross-site, so the
    // state cookie must be SameSite=None or the browser will not send it.
    pkce: false, callbackMethod: "POST", sameSite: "None",
    client(env) {
      need(env, "APPLE_SERVICE_ID", "APPLE_TEAM_ID", "APPLE_KEY_ID", "APPLE_PRIVATE_KEY");
      return new Apple(env.APPLE_SERVICE_ID, env.APPLE_TEAM_ID, env.APPLE_KEY_ID,
        pemToPkcs8(env.APPLE_PRIVATE_KEY), callback(env, "apple"));
    },
    authorizationURL(env, { state, nonce }) {
      const u = this.client(env).createAuthorizationURL(state, ["email"]);
      u.searchParams.set("response_mode", "form_post");
      u.searchParams.set("nonce", nonce);
      return u;
    },
    async identity(env, { code, nonce }) {
      const tokens = await this.client(env).validateAuthorizationCode(code);
      const c = checkIdToken(decodeIdToken(tokens.idToken()), {
        iss: "https://appleid.apple.com", aud: env.APPLE_SERVICE_ID, nonce });
      // The email may be a private relay address; it still reaches the reader.
      return contactFromEmail(c.sub, c.email, truthy(c.email_verified));
    },
  },

  facebook: {
    pkce: false, callbackMethod: "GET", sameSite: "Lax",
    client(env) {
      need(env, "FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET");
      return new Facebook(env.FACEBOOK_APP_ID, env.FACEBOOK_APP_SECRET, callback(env, "facebook"));
    },
    authorizationURL(env, { state }) {
      // `public_profile` is granted implicitly by Facebook Login; only the id is read from it.
      return this.client(env).createAuthorizationURL(state, ["email"]);
    },
    async identity(env, { code }) {
      const tokens = await this.client(env).validateAuthorizationCode(code);
      const at = tokens.accessToken();
      const proof = await hmacHex(env.FACEBOOK_APP_SECRET, at);
      const me = await getJson(`https://graph.facebook.com/v21.0/me?fields=id,email&appsecret_proof=${proof}`,
        { authorization: `Bearer ${at}` });
      // Facebook does not say whether the address was confirmed: treated as unverified.
      return contactFromEmail(String(me.id), me.email, false);
    },
  },

  x: {
    pkce: true, callbackMethod: "GET", sameSite: "Lax",
    client(env) {
      need(env, "X_CLIENT_ID", "X_CLIENT_SECRET");
      return new Twitter(env.X_CLIENT_ID, env.X_CLIENT_SECRET, callback(env, "x"));
    },
    authorizationURL(env, { state, verifier }) {
      // users.read needs tweet.read alongside it; users.email returns confirmed_email
      // only if the app has been granted the email permission.
      return this.client(env).createAuthorizationURL(state, verifier, ["users.read", "tweet.read", "users.email"]);
    },
    async identity(env, { code, verifier }) {
      const tokens = await this.client(env).validateAuthorizationCode(code, verifier);
      const me = await getJson("https://api.x.com/2/users/me?user.fields=confirmed_email",
        { authorization: `Bearer ${tokens.accessToken()}` });
      // X also returns the display `name`: it is never read. The `username` is
      // offered as the default label (owner, 2026-09-29) and is stored only if
      // the reader keeps it as a forecast's label; until then it lives in a
      // signed cookie in the reader's own browser (auth.js).
      return { ...contactFromEmail(String(me.data.id), me.data.confirmed_email, Boolean(me.data.confirmed_email)),
        handle: handleLabel(me.data.username) ? me.data.username : null };
    },
  },

  microsoft: {
    pkce: true, callbackMethod: "GET", sameSite: "Lax",
    client(env) {
      need(env, "MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET");
      return new MicrosoftEntraId(env.MICROSOFT_TENANT || "common", env.MICROSOFT_CLIENT_ID,
        env.MICROSOFT_CLIENT_SECRET, callback(env, "microsoft"));
    },
    authorizationURL(env, { state, verifier, nonce }) {
      const u = this.client(env).createAuthorizationURL(state, verifier, ["openid", "email"]);
      u.searchParams.set("nonce", nonce);
      return u;
    },
    async identity(env, { code, verifier, nonce }) {
      const tokens = await this.client(env).validateAuthorizationCode(code, verifier);
      const c = checkIdToken(decodeIdToken(tokens.idToken()), {
        // Multi-tenant issuer: https://login.microsoftonline.com/<tid>/v2.0
        iss: (iss, cl) => typeof cl.tid === "string" && iss === `https://login.microsoftonline.com/${cl.tid}/v2.0`,
        aud: env.MICROSOFT_CLIENT_ID, nonce });
      // `sub` is pairwise per app and stable. The `email` claim is not verified
      // by Microsoft for every account type; preferred_username is never used.
      return contactFromEmail(c.sub, c.email, false);
    },
  },
};

function contactFromEmail(sub, email, verified) {
  const ok = typeof email === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
  return ok
    ? { sub, contact_kind: "email", contact: email.toLowerCase(), contact_verified: verified ? 1 : 0 }
    : { sub, contact_kind: null, contact: null, contact_verified: 0 };
}
