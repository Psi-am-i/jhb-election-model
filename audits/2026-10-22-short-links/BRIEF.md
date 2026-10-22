# Short links: email, Reddit, YouTube, radio, and links to Your Forecast (22 October 2026)

Owner, 2026-10-22, on "An email short link (`/e`) and short links that land on
Your Forecast": "yes". Channels kept: Instagram, Reddit, radio, YouTube, X;
LinkedIn and Facebook dropped. Written before the code; not amended after.

1. New short paths, counted like the others (one arrival log line and one
   Analytics Engine point, channel and host only): `/e` email, `/r` Reddit,
   `/yt` YouTube, `/fm` radio. They land on `/` like `/x`.
2. Every short path has a twin ending in `p` that lands on `/your-forecast/`
   and logs the same channel with `_prediction` added: `/gop`, `/xp`,
   `/igp`, `/ep`, `/rp`, `/ytp`, `/fmp` (and `/lip`, `/fbp`, `/gp`, kept for
   symmetry while the paths exist). One table in `src/worker.js` holds path,
   channel and landing page; nothing else lists them.
3. `/li` and `/fb` stay (old links keep working); nothing new uses them.
4. `docs-public/privacy.md`'s list of short links names the new ones.
5. Checks: the worker tests for the table (every path redirects to its
   landing page and logs its channel; an unknown path is not counted), then
   the DEPLOY-UAT step 2 loop extended to the new paths on the Version URL.
