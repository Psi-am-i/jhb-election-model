// Sign in, then consent. Two screens in one modal dialog.
//
// Everything the consent screen SAYS comes from js/consent-terms.js, and the
// body it posts is built there too (consentPayload), so the page and the
// server (worker-api/src/consent.js) accept exactly the same keys and the
// wording version recorded is the hash of the text shown. Nothing here adds
// wording of its own; test/node/consent-screen.test.js holds that.
//
// POPIA design (to be checked by counsel; see README "Legal"):
//  * Owner, 2026-09-29: a saved forecast is a PREDICTION, treated as ordinary
//    personal information. The protections stay: explicit consent to store it
//    (a separate, unticked, required box), 18+ confirmed, deletion at any time.
//  * "Contact me if I win" and "send me updates" are SEPARATE, UNTICKED and
//    OPTIONAL. Saving works with both unticked (s69 opt-in).
//  * No name is collected. A shared prediction shows a label (js/labels.js).
//  * An email is stored only once confirmed: one confirmation link, then
//    nothing unless it is used.

import { session, signIn, recordConsent } from "./api-stub.js";
import { esc } from "./common.js";
import { consentTerms, consentPayload, wordingVersion, deletionDateText, PROVIDER_LABELS } from "./consent-terms.js";

// Sign-in options (owner, DESIGN-decided §9). Instagram has no personal-account
// sign-in (Meta closed it in December 2024); Facebook covers Meta users.
export const PROVIDERS = ["google", "apple", "microsoft", "facebook", "x"];

let dlg;

function build() {
  dlg = document.createElement("dialog");
  dlg.className = "sheet";
  dlg.setAttribute("aria-labelledby", "auth-title");
  document.body.appendChild(dlg);
}

function screenProviders(resolve) {
  dlg.innerHTML = `
  <div class="dh"><h2 id="auth-title">Sign in to save your prediction</h2>
    <button class="x" type="button" data-close aria-label="Close">×</button></div>
  <div class="db">
    <p style="font-size:14px;margin-bottom:12px">Signing in keeps your prediction, gives it a link to share,
      and lets us score it against the result. You choose what else we may do on the next screen.</p>
    <div class="providers">
      ${PROVIDERS.map(k => `<button class="btn" type="button" data-p="${k}">Continue with ${esc(PROVIDER_LABELS[k])}</button>`).join("")}
    </div>
    <p class="stubnote"><b>Prototype:</b> these buttons call a stub. No provider is contacted, no email is sent.</p>
  </div>`;
  dlg.querySelectorAll("[data-p]").forEach(b => b.addEventListener("click", async () => {
    const s = await signIn(b.dataset.p);
    screenConsent(resolve, s);
  }));
  dlg.querySelector("[data-p]").focus();
}

// The consent screen's HTML, from the terms and the sign-in state only. Pure,
// so a test can check that every word shown is in the hashed terms.
//   s: { provider, contact_confirmed, unconfirmed_contact }
export function consentScreenHTML(s, terms) {
  const askContact = !s.contact_confirmed;
  return `
  <div class="dh"><h2 id="auth-title">${esc(terms.title)}</h2>
    <button class="x" type="button" data-close aria-label="${esc(terms.cancel)}">×</button></div>
  <form class="db consent" id="cform" novalidate>
    <p>${esc(terms.signedInWith)} ${esc(PROVIDER_LABELS[s.provider] || s.provider)}.</p>

    <div class="req">
      <p style="color:var(--ink);font-weight:600;margin-bottom:6px">${esc(terms.requiredHeading)}</p>
      <label class="box"><input type="checkbox" id="c-store" required><span><b>${esc(terms.boxes.store)}</b></span></label>
      <label class="box" style="margin-top:8px"><input type="checkbox" id="c-age" required><span><b>${esc(terms.boxes.age18)}</b></span></label>
    </div>

    <div>
      <p style="color:var(--ink);font-weight:600;margin-bottom:6px">${esc(terms.optionalHeading)}</p>
      <label class="box"><input type="checkbox" id="c-win"><span>${esc(terms.boxes.contact_if_win)}</span></label>
      <label class="box" style="margin-top:6px"><input type="checkbox" id="c-upd"><span>${esc(terms.boxes.updates)}</span></label>
    </div>
    ${askContact ? `<div><label for="cemail" style="color:var(--ink);font-weight:600">${esc(terms.contactLabel)}</label>
      <input id="cemail" type="email" autocomplete="email" style="width:100%;margin-top:4px" value="${esc(s.unconfirmed_contact || "")}" aria-describedby="cemailhelp">
      <p id="cemailhelp" style="font-size:12.5px;color:var(--ink-3);margin-top:3px">${esc(terms.contactHelp)}</p></div>` : ""}

    <dl>
      ${terms.facts.map(([dt, dd]) => `<dt>${esc(dt)}</dt><dd>${esc(dd)}</dd>`).join("\n      ")}
    </dl>
    <p style="font-size:12.5px"><a href="../privacy-placeholder.html">${esc(terms.links.notice)}</a> ·
      <a href="../privacy-placeholder.html#officer">${esc(terms.links.officer)}</a> ·
      <a href="../privacy-placeholder.html#competition">${esc(terms.links.competition)}</a></p>
    <p class="err" id="cerr" role="alert"></p>
    <div class="row">
      <button class="btn primary" type="submit">${esc(terms.submit)}</button>
      <button class="btn" type="button" data-close>${esc(terms.cancel)}</button>
    </div>
  </form>`;
}

async function screenConsent(resolve, s) {
  const terms = consentTerms({ deletionDate: deletionDateText(s.deletion_date) });
  const version = await wordingVersion(terms);
  dlg.innerHTML = consentScreenHTML(s, terms);
  dlg.querySelector("#cform").addEventListener("submit", async e => {
    e.preventDefault();
    const q = sel => dlg.querySelector(sel);
    const contact = q("#cemail")?.value.trim() || "";
    const errs = [];
    if (contact && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)) errs.push("enter an email address like name@example.com, or leave it empty");
    if (!q("#c-store").checked) errs.push("tick the box to save your prediction");
    if (!q("#c-age").checked) errs.push("confirm you are 18 or older");
    if (errs.length) { q("#cerr").textContent = "To save, " + errs.join(", ") + "."; return; }
    const body = consentPayload({ store: true, age18: true, contact_if_win: q("#c-win").checked,
      updates: q("#c-upd").checked, contact, wording_version: version });
    try {
      resolve(await recordConsent(body)); dlg.close();
    } catch (err) {
      q("#cerr").textContent = String(err.message || err);
    }
  });
  dlg.querySelector("#c-store").focus();
}

// Resolves with the session once consent is recorded, or null if the reader
// closes the dialog. Focus returns to whatever opened it.
export function ensureConsent() {
  const s = session();
  if (s?.consent?.store) return Promise.resolve(s);
  if (!dlg) build();
  const opener = document.activeElement;
  return new Promise(resolve => {
    let done = false;
    const fin = v => { if (!done) { done = true; resolve(v); } };
    dlg.onclick = e => { if (e.target.closest("[data-close]")) { dlg.close(); } };
    dlg.onclose = () => { fin(session()?.consent?.store ? session() : null); opener?.focus?.(); };
    if (s && !s.consent) screenConsent(fin, s); else screenProviders(fin);
    dlg.showModal();
  });
}
