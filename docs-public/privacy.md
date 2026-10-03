# Privacy

## Who is responsible

The responsible party for this site under the Protection of Personal
Information Act (POPIA) is the site's author, Simon Davis, 91 St Patrick Road, Johannesburg 2198.

Contact: [psi@whysoserious.city](mailto:psi@whysoserious.city).

<!-- analytics -->
## What is measured

The site counts its readers with **Cloudflare Web Analytics**. It sets no
cookie, so there is no consent banner. Cloudflare's description of it ([Cloudflare Web Analytics](https://www.cloudflare.com/web-analytics/)):
"Cloudflare Web Analytics does not use any client-side state, such as cookies
or localStorage, to collect usage metrics. We also don't 'fingerprint'
individuals via their IP address, User Agent string, or any other data for the
purpose of displaying analytics."

For each page view it records:

- the page's address on this site, without any part after a `?`;
- the site that linked to it, if any;
- your country;
- your device type, browser and operating system;
- how long the page took to load and display.
<!-- /analytics -->
<!-- no-analytics -->
## What is measured

The pages carry no analytics script and count no page views. The short links
described below are the only count the site keeps.
<!-- /no-analytics -->

## Which link brought you here

Links in this site's advertising and social posts use short addresses, one per
channel: `/go` on the billboard, `/x`, `/li`, `/fb` and `/ig` for social posts,
and `/g` for Google Ads. Each forwards to the home page and writes one log line
naming the channel and the site's own address, and nothing about the visitor.
The site counts those lines by channel.

Cloudflare's [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
holds those lines, with the metadata Cloudflare attaches to each, and any error
the site's server code raises. It is set not to record each request, and keeps
every entry for at most seven days.

The same count (the channel and the site's address for each arrival, and
nothing about the visitor) is also kept in Cloudflare's
[Workers Analytics Engine](https://developers.cloudflare.com/analytics/analytics-engine/),
which deletes it after three months.

## Shared forecasts

A forecast you make on [your forecast](your-forecast/) lives only in its link.
When you share it, three things happen on the site's server, and none of them
keeps the forecast or the name in it.

- **The seal.** The page sends the forecast and its name to the server, which
  signs them with the time, using a key only the server holds, and returns the
  signature for the link to carry. Anyone opening the link can then see that
  it was sealed and when. The server keeps no record of what it signed.
- **The preview image.** A chat app shown the link fetches an image the server
  draws from the link. The image is kept in Cloudflare's cache, which deletes
  it on its own.
- **The count.** Shared links go out as `/s/` addresses. Each forwards to the
  forecast and writes one log line and one Analytics Engine data point naming
  "share", the button used (WhatsApp, X, copy or the phone's share menu) and
  the site's own address, as the short links above do.

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

The light/dark switch in the menu bar saves your choice in your browser's local
storage under the name `theme`, so the next page opens the same way. It stays
on your device and is not sent to the site.

## Who serves the site, and where

The site is hosted and delivered by Cloudflare, Inc. It processes the IP
address and request details of every visit to deliver pages and protect the
site from abuse, as set out in the
[Cloudflare privacy policy](https://www.cloudflare.com/privacypolicy/).

Cloudflare is a United States company, and its network handles requests in
data centres outside South Africa, so this data leaves the country. The transfer
rests on a binding agreement, Cloudflare's
[Data Processing Addendum](https://www.cloudflare.com/cloudflare-customer-dpa/),
under which it processes personal data only to provide its service to this
site and must keep that data secure. POPIA permits a transfer abroad to a
recipient bound by an agreement of that kind.

## Your rights

Under POPIA you may:

- ask whether the site holds personal data about you, and for a copy of it;
- ask for that data to be corrected or deleted;
- object to its processing.

Send a request to [psi@whysoserious.city](mailto:psi@whysoserious.city). The
site stores nothing that names a visitor; the records described above are held
by Cloudflare.

If you are not satisfied with the answer, you may complain to the
[Information Regulator](https://inforegulator.org.za/), South Africa's
regulator for POPIA.
