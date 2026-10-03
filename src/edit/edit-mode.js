/*
 * Edit mode's overlay. Served by src/edit_mode.py at /__edit/ and injected into
 * each page as it is served; never copied into site/ (deploy_check refuses a
 * site that carries it). Every rule about what an edit may do is enforced by
 * the server; this file only draws the buttons, the editor and the review.
 */
(() => {
  "use strict";
  const API = "/__edit/api/";
  const ATTR = "data-edit-block";
  const page = location.pathname;

  async function call(name, body) {
    const opt = body === undefined
      ? { headers: { "X-Edit-Mode": "1" } }
      : { method: "POST", body: JSON.stringify(body),
          headers: { "Content-Type": "application/json", "X-Edit-Mode": "1" } };
    const res = await fetch(API + name, opt);
    let data = {};
    try { data = await res.json(); } catch (_) { /* not JSON */ }
    return { ok: res.ok, data };
  }

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function button(label, cls, onclick) {
    const b = el("button", cls || "ed-act", label);
    b.type = "button";
    b.addEventListener("click", (ev) => { ev.preventDefault(); ev.stopPropagation(); onclick(ev); });
    return b;
  }

  // ---- the toolbar ------------------------------------------------------
  const bar = el("div", "ed-bar");
  const count = el("span", "ed-count", "");
  bar.append(el("strong", "", "Edit mode"), count,
             button("Review changes", "ed-act ed-primary", openReview));
  const panel = el("aside", "ed-panel");
  panel.hidden = true;

  async function refreshCount() {
    const { data } = await call("status");
    const n = (data.pending || []).length;
    count.textContent = n ? `${n} edited block${n > 1 ? "s" : ""} not yet applied` : "no edits";
    for (const e of document.querySelectorAll(`[${ATTR}]`)) {
      const ids = e.getAttribute(ATTR).split(" ");
      e.classList.toggle("ed-pending", ids.some((i) => (data.pending || []).includes(i)));
    }
  }

  function showPanel(title, ...children) {
    panel.replaceChildren(el("div", "ed-head"));
    panel.firstChild.append(el("h2", "", title), button("Close", "ed-act", () => { panel.hidden = true; }));
    panel.append(...children);
    panel.hidden = false;
    panel.scrollTop = 0;
  }

  function messages(list, cls) {
    const ul = el("ul", "ed-msgs " + (cls || ""));
    for (const m of list || []) ul.append(el("li", "", m));
    return ul;
  }

  // ---- the editor -------------------------------------------------------
  function chip(seg) {
    const c = el("span", "ed-chip ed-" + seg.t);
    c.contentEditable = "false";
    c.dataset.raw = seg.v;
    c.title = seg.v;
    let label = seg.label || seg.name;
    if (seg.t === "token") {
      const live = document.querySelector(`[data-token="${CSS.escape(seg.name)}"]`);
      label = (live ? live.textContent.trim() + " · " : "") + seg.name;
    }
    c.append(el("span", "ed-chip-label", label),
             button("×", "ed-x", () => c.remove()));
    c.lastChild.title = seg.t === "token" ? "Delete this figure" : "Delete this tag";
    return c;
  }

  function fill(editor, segs) {
    editor.replaceChildren(...segs.map((s) => s.t === "text" ? document.createTextNode(s.v) : chip(s)));
  }

  function serialize(node) {
    let out = "";
    for (const n of node.childNodes) {
      if (n.nodeType === Node.TEXT_NODE) out += n.nodeValue;
      else if (n.nodeType === Node.ELEMENT_NODE) {
        if (n.dataset.raw !== undefined) out += n.dataset.raw;
        else if (n.tagName === "BR") out += "\n";
        else out += (n.tagName === "DIV" || n.tagName === "P" ? "\n" : "") + serialize(n);
      }
    }
    return out;
  }

  async function openEditor(id) {
    const { ok, data } = await call("block?id=" + encodeURIComponent(id));
    if (!ok) return showPanel("Edit", messages(data.problems, "ed-bad"));
    const editor = el("div", "ed-editor");
    editor.setAttribute("contenteditable", "plaintext-only");
    if (editor.contentEditable !== "plaintext-only") editor.contentEditable = "true";
    editor.spellcheck = true;
    fill(editor, data.segments);
    const raw = el("textarea", "ed-raw");
    raw.hidden = true;
    const out = el("div", "ed-out");
    const rawToggle = button("Raw text", "ed-act", async () => {
      if (raw.hidden) {
        raw.value = serialize(editor);
        raw.hidden = false; editor.hidden = true; rawToggle.textContent = "Chips";
      } else {
        const r = await call("segments", { id, text: raw.value });
        if (r.ok) fill(editor, r.data.segments);
        raw.hidden = true; editor.hidden = false; rawToggle.textContent = "Raw text";
      }
    });
    const save = button("Save", "ed-act ed-primary", async () => {
      const text = raw.hidden ? serialize(editor) : raw.value;
      const r = await call("save", { id, text, page });
      if (!r.ok) {
        out.replaceChildren(el("p", "ed-bad", "Not saved."), messages(r.data.problems, "ed-bad"));
        return;
      }
      const nums = r.data.numbers || [];
      out.replaceChildren(el("p", "ed-good", r.data.saved ? "Saved. Nothing is written to the source until you apply." : "No change from the source."));
      if (nums.length) out.append(el("p", "ed-warn", `New typed number${nums.length > 1 ? "s" : ""}: ${nums.join(", ")}. Review changes to make each a token, register it or remove it.`));
      refreshCount();
    });
    const discard = button("Discard edit", "ed-act", async () => {
      await call("discard", { id });
      fill(editor, (await call("block?id=" + encodeURIComponent(id))).data.segments);
      out.replaceChildren(el("p", "", "Back to the source text."));
      refreshCount();
    });
    const meta = el("p", "ed-meta", `${data.source} · ${data.kind} · block ${data.id}`);
    const help = el("p", "ed-help",
      "Figures and tags are locked chips: keep them or delete them with ×. " +
      "Raw text shows them as they are in the source; the server refuses any change inside one.");
    const row = el("div", "ed-row");
    row.append(save, rawToggle, discard);
    showPanel("Edit this block", meta, help, editor, raw, row, out);
    editor.focus();
  }

  // ---- the review -------------------------------------------------------
  function diffView(text) {
    const pre = el("pre", "ed-diff");
    for (const line of text.split("\n")) {
      const cls = line.startsWith("+++") || line.startsWith("---") ? "ed-dh"
        : line.startsWith("+") ? "ed-add" : line.startsWith("-") ? "ed-del"
        : line.startsWith("@@") ? "ed-dh" : "";
      pre.append(el("span", cls, line + "\n"));
    }
    return pre;
  }

  function numberRow(edit, n, kinds) {
    const box = el("div", "ed-num");
    box.append(el("p", "", ""));
    box.firstChild.append(el("strong", "", n.value), ` is typed, not a token: …${n.context}…`);
    if (n.was_fixed) box.append(el("p", "ed-warn", "It was a registered fixed fact, and the edit changed the words its entry in stats.toml names."));
    const opts = el("div", "ed-row");
    const form = el("div", "ed-form");
    const act = async (body) => {
      const r = await call(body.register ? "register" : "resolve", { id: edit.id, value: n.value, ...body });
      if (!r.ok) form.replaceChildren(messages(r.data.problems, "ed-bad"));
      else openReview();
    };
    opts.append(
      button("Make it a token", "ed-act", () => {
        form.replaceChildren();
        for (const c of n.candidates) {
          form.append(button(`use {{${c.name}}} (shows ${c.display})`, "ed-act",
                             () => act({ action: "token", token: c.name })));
        }
        if (!n.candidates.length) form.append(el("p", "", "No token shows this value now. Name one from content/joburg/stats.toml:"));
        const name = el("input", "ed-in");
        name.placeholder = "token name";
        form.append(name, button("Use", "ed-act", () => act({ action: "token", token: name.value.trim() })));
      }),
      button("Register it", "ed-act", () => {
        const ctx = el("input", "ed-in"); ctx.value = n.context;
        const src = el("input", "ed-in"); src.placeholder = "where the number comes from (required)";
        const kind = el("select", "ed-in");
        for (const k of kinds) kind.append(new Option(k, k));
        form.replaceChildren(el("label", "", "Context (words around it, as on the page)"), ctx,
                             el("label", "", "Source"), src, el("label", "", "Kind"), kind,
                             button("Register in stats.toml", "ed-act ed-primary",
                                    () => act({ register: true, context: ctx.value, source: src.value, kind: kind.value })));
      }),
      button("Remove it", "ed-act", () => act({ action: "remove" })));
    box.append(opts, form);
    return box;
  }

  async function openReview() {
    const { data } = await call("review");
    const body = el("div", "");
    if (!data.edits || !data.edits.length) body.append(el("p", "", "No edits yet. Use the edit buttons on the page."));
    for (const e of data.edits || []) {
      const sec = el("section", "ed-edit");
      sec.append(el("h3", "", e.source ? `${e.source} · ${e.kind}` : "Refused"));
      if (e.problems && e.problems.length) sec.append(el("p", "ed-bad", "Refused:"), messages(e.problems, "ed-bad"));
      for (const n of e.numbers || []) sec.append(numberRow(e, n, data.kinds || []));
      if (e.id) sec.append(button("Open in editor", "ed-act", () => openEditor(e.id)));
      body.append(sec);
    }
    if (data.diff) body.append(el("h3", "", "What Apply writes"), diffView(data.diff));
    const apply = button("Apply to the source files", "ed-act ed-primary", async () => {
      const r = await call("apply", {});
      if (!r.ok) return body.append(messages(r.data.problems, "ed-bad"));
      showPanel("Applied",
        el("p", "ed-good", `Written: ${r.data.written.join(", ")}.`),
        el("p", "", "Now run the normal build, then reload this page:"),
        el("pre", "ed-cmd", r.data.rebuild), diffView(r.data.diff));
      refreshCount();
    });
    apply.disabled = !data.can_apply;
    body.append(el("div", "ed-row"));
    body.lastChild.append(apply);
    if (!data.can_apply && data.edits && data.edits.length) {
      body.append(el("p", "ed-warn", "Apply waits until every refused edit and typed number above is dealt with."));
    }
    showPanel("Review changes", body);
  }

  // ---- buttons on the page ----------------------------------------------
  function init() {
    for (const e of document.querySelectorAll(`[${ATTR}]`)) {
      const ids = e.getAttribute(ATTR).split(" ");
      ids.forEach((id, k) => {
        const label = ids.length > 1 ? `edit ${k + 1}/${ids.length}` : "edit";
        const b = button(label, "ed-btn", () => openEditor(id));
        b.title = ids.length > 1
          ? "These words come from more than one place in the sources; the editor names each"
          : "Edit this block's source";
        e.append(b);
      });
    }
    document.body.append(bar, panel);
    refreshCount();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
