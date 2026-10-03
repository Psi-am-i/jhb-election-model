// The ward maps (src/render_map.py, src/hex_cartogram.py; src/css/maps.css).
// It shows the tooltip a ward or a bar segment already carries (its data-tip,
// which the number scan has read) and switches between the land map and the
// equal-ward map. It writes no figure of its own.
(function () {
  function follow(tip, e) {
    var t = e.target.getAttribute && e.target.getAttribute("data-tip");
    if (!t) { tip.hidden = true; return; }
    tip.textContent = t;
    tip.hidden = false;
    tip.style.left = (e.clientX + 14) + "px";
    tip.style.top = (e.clientY + 14) + "px";
  }
  // The land map's tooltip follows every data-tip on the page: the wards,
  // the council bar under the map and the two-ballots strip.
  var maptip = document.getElementById("maptip");
  if (maptip) {
    document.addEventListener("mousemove", function (e) { follow(maptip, e); });
    document.addEventListener("click", function (e) { follow(maptip, e); });
    document.addEventListener("mouseleave", function () { maptip.hidden = true; });
  }
  // The equal-ward map's own.
  var hextip = document.getElementById("hextip");
  var hex = document.getElementById("wardhexmap");
  if (hextip && hex) {
    hex.addEventListener("mousemove", function (e) { follow(hextip, e); });
    hex.addEventListener("click", function (e) { follow(hextip, e); });
    hex.addEventListener("mouseleave", function () { hextip.hidden = true; });
  }
  // The Normal / Equal Sized switch: shows one map's section, hides the other.
  var buttons = document.querySelectorAll(".maptoggle button");
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var show = b.getAttribute("data-show");
      document.querySelectorAll("details[data-map]").forEach(function (d) {
        d.hidden = d.getAttribute("data-map") !== show;
      });
      buttons.forEach(function (o) {
        var on = o.getAttribute("data-show") === show;
        o.classList.toggle("on", on);
        o.setAttribute("aria-pressed", on ? "true" : "false");
      });
    });
  });
})();
