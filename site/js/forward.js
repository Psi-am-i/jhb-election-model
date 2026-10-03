// Forwards a link to a section this page does not hold, rather than dropping
// the reader at the top. The page names where in the script tag's data-to:
//   * the home page, to "forecast": until 2026-09 the forecast sheet WAS the
//     landing page, so links already shared point at "/#section";
//   * /forecast, to "nobody-will-win": the 8 August article used to share it.
(function () {
  var to = document.currentScript && document.currentScript.getAttribute("data-to");
  var id = decodeURIComponent(location.hash.slice(1));
  if (to && id && !document.getElementById(id)) location.replace(to + "#" + encodeURIComponent(id));
})();
