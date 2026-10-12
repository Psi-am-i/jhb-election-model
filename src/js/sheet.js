// The forecast sheet's controls (/forecast and /nobody-will-win). It only
// shows, hides, opens and closes what the build already wrote; it never
// writes a figure (every number is a build-time token).
(function () {
  // The coalition table's filter.
  var rows = Array.prototype.slice.call(document.querySelectorAll("#coalitions tr[data-parties]"));
  var gw = Array.prototype.slice.call(document.querySelectorAll(".govfilter .gw"));
  var gx = Array.prototype.slice.call(document.querySelectorAll(".govfilter .gx"));
  var more = document.getElementById("govMore");
  var first = gw[0];
  if (first) {
    var opts = Array.prototype.slice.call(first.options).slice(1);
    gw.slice(1).concat(gx).forEach(function (s) {
      opts.forEach(function (o) { s.appendChild(new Option(o.text, o.value)); });
    });
  }
  var LIMIT = 15;
  function apply(withs, withouts, all) {
    withs = withs.filter(Boolean); withouts = withouts.filter(Boolean);
    var filtered = withs.length > 0 || withouts.length > 0 || all, shown = 0;
    rows.forEach(function (r) {
      var ps = r.getAttribute("data-parties").split(" ");
      var ok = withs.every(function (w) { return ps.indexOf(w) >= 0; }) &&
               withouts.every(function (x) { return ps.indexOf(x) < 0; });
      if (ok && !filtered && shown >= LIMIT) ok = false;
      if (ok) shown++;
      r.hidden = !ok;
    });
    if (more) more.hidden = filtered;
  }
  function set(sel, vals) { sel.forEach(function (s, i) { s.value = vals[i] || ""; }); }
  if (rows.length) apply([], [], false);
  var go = document.getElementById("govGo");
  if (go) go.addEventListener("click", function () {
    apply(gw.map(function (s) { return s.value; }), gx.map(function (s) { return s.value; }), false);
  });
  document.querySelectorAll(".govfilter button[data-with]").forEach(function (b) {
    b.addEventListener("click", function () {
      var w = b.getAttribute("data-with").split(" ").filter(Boolean);
      var x = b.getAttribute("data-without").split(" ").filter(Boolean);
      set(gw, w); set(gx, x);
      apply(w, x, b.hasAttribute("data-all"));
    });
  });
  if (more) more.addEventListener("click", function () { apply([], [], true); });

  // "collapse all" / "expand all" on each band of sections.
  document.querySelectorAll(".bandbtn").forEach(function (b) {
    b.addEventListener("click", function () {
      var els = document.querySelectorAll('details.rollup[data-band="' + b.dataset.band + '"]');
      var anyOpen = Array.prototype.some.call(els, function (d) { return d.open; });
      els.forEach(function (d) { d.open = !anyOpen; });
      b.textContent = anyOpen ? "expand all" : "collapse all";
    });
  });
})();
