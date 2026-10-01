# Privacy

## What is measured

The site counts its readers with **Cloudflare Web Analytics**. It sets no
cookie, which is why there is no consent banner. Cloudflare's description of
it ([Cloudflare Web Analytics](https://www.cloudflare.com/web-analytics/)):
"Cloudflare Web Analytics does not use any client-side state, such as cookies
or localStorage, to collect usage metrics. We also don't 'fingerprint'
individuals via their IP address, User Agent string, or any other data for the
purpose of displaying analytics."

For each page view it records:

- the page's address on this site, without any part after a `?`, which Web
  Analytics does not log;
- the site that linked to it, if any;
- your country;
- your device type, browser and operating system;
- how long the page took to load and draw.

## Which link brought you here

Links in this site's advertising and social posts use short addresses, one per
channel: `/go` on the billboard, `/x`, `/li`, `/fb` and `/ig` for social posts,
and `/g` for Google Ads. Each forwards to the home page. When it does, the
site's server code writes one log line naming the channel, and nothing about
the visitor. The site counts those lines to see which channels bring readers.

Cloudflare's [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/),
which holds those lines, also records each request the site's server code
handles, with the request's details, and keeps every record for at most seven
days.

## Network error reports

Cloudflare's response headers `NEL` and `Report-To` ask your browser to report
failed connections to the site, not successful ones, to Cloudflare's
[Network Error Logging](https://developers.cloudflare.com/network-error-logging/)
service.

## What is not collected

- No accounts, sign-in or forms. If that changes, this page changes with it.
- No advertising trackers and no Google tags.
- No personal data is sold, or shared with advertisers.

## What your browser keeps

If you use the light/dark switch in the menu bar, your choice is saved in your
browser's local storage under the name `theme`, so the next page opens the same
way. It stays on your device and is never sent to the site.

## Who serves the site

The site is hosted and delivered by Cloudflare. Like any web host, it processes
the IP address and request details of every visit in order to deliver pages and
protect the site from abuse. Its handling of that data is set out in the
[Cloudflare privacy policy](https://www.cloudflare.com/privacypolicy/).

## Contact

Questions about this page: [psi@whysoserious.city](mailto:psi@whysoserious.city).
