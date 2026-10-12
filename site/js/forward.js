// Forwards a link to a section this page does not hold, rather than dropping
// the reader at the top. The script tag says where:
//   data-map  "id:page id:page …", sections that moved to a page of their own
//             (the owner's sweep, 2026-10-03, gave each article its own page
//             and the claims their own; a fragment never reaches the server,
//             so the Worker cannot redirect these and this script does);
//   data-to   the page to try for any other id this page lacks:
//     * the home page, to "forecast": until 2026-09 the forecast sheet WAS
//       the landing page, so links already shared point at "/#section";
//     * /forecast, to "nobody-will-win": the 8 August article used to share it.
(function () {
  var s = document.currentScript;
  var id = decodeURIComponent(location.hash.slice(1));
  if (!s || !id || document.getElementById(id)) return;
  var map = {};
  (s.getAttribute("data-map") || "").split(/\s+/).forEach(function (pair) {
    var i = pair.indexOf(":");
    if (i > 0) map[pair.slice(0, i)] = pair.slice(i + 1);
  });
  var to = map[id] || s.getAttribute("data-to");
  if (to) location.replace(to + "#" + encodeURIComponent(id));
})();
