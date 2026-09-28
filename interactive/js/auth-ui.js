// Sign in, then consent. Two screens in one modal dialog.
//
// POPIA design (to be checked by counsel — see README "Legal"):
//  * A saved forecast can reveal political persuasion, which POPIA s26 treats
//    as special personal information. The lawful basis used is the reader's
//    explicit consent (s27(1)(a)): a separate, unticked, required box that says
//    exactly that, with purpose, retention and deletion stated beside it.
//  * "Contact me if I win" and "send me updates" are SEPARATE, UNTICKED and
//    OPTIONAL. Saving works with both unticked (consent must be voluntary;
//    electronic direct marketing needs opt-in, s69).
//  * Showing the reader's name on a public page is its own required choice with
//    no default, because it publishes a view against a name.
//  * 18+ is confirmed, which also keeps children's data (s34) out.
//  * Only a display name, an email and the provider's account id are kept.

import { session, signIn, recordConsent } from "./api-stub.js";
import { cleanName, esc } from "./common.js";

const PROVIDERS = [
  ["google", "Continue with Google"],
  ["apple", "Continue with Apple"],
  ["facebook", "Continue with Facebook"],
  ["x", "Continue with X"],
];

let dlg;

function build() {
  dlg = document.createElement("dialog");
  dlg.className = "sheet";
  dlg.setAttribute("aria-labelledby", "auth-title");
  document.body.appendChild(dlg);
}

function screenProviders(resolve) {
  dlg.innerHTML = `
  <div class="dh"><h2 id="auth-title">Sign in to save your forecast</h2>
    <button class="x" type="button" data-close aria-label="Close">×</button></div>
  <div class="db">
    <p style="font-size:14px;margin-bottom:12px">Signing in keeps your forecast, gives it a link to share,
      and lets us score it against the result. You choose what else we may do on the next screen.</p>
    <div class="providers">
      ${PROVIDERS.map(([k, l]) => `<button class="btn" type="button" data-p="${k}">${l}</button>`).join("")}
    </div>
    <div class="or">or</div>
    <form id="mlform" novalidate>
      <label for="mlemail" style="font-size:13.5px;color:var(--ink)">Email me a sign-in link</label>
      <div class="urlrow"><input id="mlemail" type="email" autocomplete="email" inputmode="email"
        placeholder="you@example.com" required>
        <button class="btn" type="submit">Send link</button></div>
      <p class="err" id="mlerr" role="alert"></p>
    </form>
    <p class="stubnote"><b>Prototype:</b> these buttons call a stub. No provider is contacted, no email is sent.</p>
  </div>`;
  dlg.querySelectorAll("[data-p]").forEach(b => b.addEventListener("click", async () => {
    const s = await signIn(b.dataset.p);
    screenConsent(resolve, s);
  }));
  dlg.querySelector("#mlform").addEventListener("submit", async e => {
    e.preventDefault();
    const v = dlg.querySelector("#mlemail").value.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      dlg.querySelector("#mlerr").textContent = "Enter an email address like name@example.com.";
      return;
    }
    dlg.querySelector(".db").innerHTML = `
      <p style="font-size:15px;color:var(--ink)">We've sent a sign-in link to <b>${esc(v)}</b>.</p>
      <p style="font-size:13.5px;margin-top:8px">It works once and expires in 15 minutes. Your forecast stays on this page while you look.</p>
      <p class="stubnote" style="margin-top:12px"><b>Prototype:</b> nothing was sent. Continue as if you had clicked the link.</p>
      <div class="row" style="margin-top:14px"><button class="btn primary" type="button" id="mlgo">I clicked the link</button></div>`;
    dlg.querySelector("#mlgo").addEventListener("click", async () => {
      const s = await signIn("email", v);
      screenConsent(resolve, s);
    });
    dlg.querySelector("#mlgo").focus();
  });
  dlg.querySelector("[data-p]").focus();
}

function screenConsent(resolve, s) {
  const needEmail = !s.email;
  dlg.innerHTML = `
  <div class="dh"><h2 id="auth-title">Before we save your forecast</h2>
    <button class="x" type="button" data-close aria-label="Close">×</button></div>
  <form class="db consent" id="cform" novalidate>
    <p>Signed in with ${esc({ google: "Google", apple: "Apple", facebook: "Facebook", x: "X", email: "an email link" }[s.provider])}.</p>

    <div>
      <label for="dname" style="color:var(--ink);font-weight:600">Your name as others will see it</label>
      <input id="dname" type="text" maxlength="40" autocomplete="nickname" value="${esc(s.name || "")}"
        style="width:100%;margin-top:4px" aria-describedby="dnamehelp">
      <p id="dnamehelp" style="font-size:12.5px;color:var(--ink-3);margin-top:3px">Up to 40 characters. First name and an initial is plenty.</p>
    </div>
    ${needEmail ? `<div><label for="cemail" style="color:var(--ink);font-weight:600">Your email</label>
      <input id="cemail" type="email" autocomplete="email" style="width:100%;margin-top:4px">
      <p style="font-size:12.5px;color:var(--ink-3);margin-top:3px">X did not give us an email. We need one to let you delete your forecast or tell you if you win.</p></div>` : ""}

    <fieldset class="req" style="border-left-width:3px">
      <legend style="color:var(--ink);font-weight:600;padding:0 4px">On shared links and images, show</legend>
      <label class="box"><input type="radio" name="showname" value="1"><span>my name</span></label>
      <label class="box"><input type="radio" name="showname" value="0"><span>"A reader" instead of my name</span></label>
    </fieldset>

    <div class="req">
      <label class="box"><input type="checkbox" id="c-store" required>
        <span><b>Save my forecast and link it to me.</b> A forecast can show which parties I expect or want to govern,
        which the law treats as information about my political views. I agree to it being kept for the purposes below.</span></label>
      <label class="box" style="margin-top:8px"><input type="checkbox" id="c-age" required>
        <span><b>I am 18 or older.</b></span></label>
    </div>

    <div>
      <p style="color:var(--ink);font-weight:600;margin-bottom:6px">Optional — leave these unticked and your forecast is still saved</p>
      <label class="box"><input type="checkbox" id="c-win">
        <span>Email me if my forecast wins. <a href="../privacy-placeholder.html#competition">Competition rules</a></span></label>
      <label class="box" style="margin-top:6px"><input type="checkbox" id="c-upd">
        <span>Email me updates about the forecast before and after the election. Unsubscribe from any email.</span></label>
    </div>

    <dl>
      <dt>We keep</dt><dd>your display name, email, sign-in provider and account id, your forecasts, and these choices with the date.</dd>
      <dt>To</dt><dd>save and show your forecast, score it against the result on 4 November, and contact you only for what you ticked.</dd>
      <dt>Until</dt><dd><i>[retention period — owner to decide; proposed: 30 June 2027, then deleted]</i>. Updates continue only until you unsubscribe.</dd>
      <dt>Delete</dt><dd>any forecast, or everything, at any time from “My forecasts”. A deleted link stops working.</dd>
      <dt>Where</dt><dd>on Cloudflare's servers, which may be outside South Africa.</dd>
      <dt>Never</dt><dd>sold, never used for advertising, never shared except as you choose to share it.</dd>
    </dl>
    <p style="font-size:12.5px"><a href="../privacy-placeholder.html">Privacy notice</a> ·
      <a href="../privacy-placeholder.html#officer">Information Officer</a></p>
    <p class="err" id="cerr" role="alert"></p>
    <div class="row">
      <button class="btn primary" type="submit">Agree and save</button>
      <button class="btn" type="button" data-close>Don't save</button>
    </div>
  </form>`;
  dlg.querySelector("#cform").addEventListener("submit", e => {
    e.preventDefault();
    const q = sel => dlg.querySelector(sel);
    const show = dlg.querySelector('input[name="showname"]:checked');
    const name = cleanName(q("#dname").value);
    const email = needEmail ? q("#cemail").value.trim() : null;
    const errs = [];
    if (!show) errs.push("choose whether to show your name");
    if (show?.value === "1" && !name) errs.push("enter the name to show");
    if (needEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.push("enter your email");
    if (!q("#c-store").checked) errs.push("tick the box to save your forecast");
    if (!q("#c-age").checked) errs.push("confirm you are 18 or older");
    if (errs.length) { q("#cerr").textContent = "To save, " + errs.join(", ") + "."; return; }
    const out = recordConsent({ store: true, age18: true, show_name: show.value === "1",
      display_name: name, contact_if_win: q("#c-win").checked, updates: q("#c-upd").checked, email });
    resolve(out); dlg.close();
  });
  dlg.querySelector("#dname").focus();
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
