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
channel: `/go` on the billboard, `/x`, `/ig`, `/r` (Reddit), `/yt` (YouTube),
`/li` and `/fb` for social posts, `/e` in email, `/fm` on radio, and `/g` for
Google Ads. Each forwards to the home page, and the same address ending in `p`
(`/xp`, `/ep` and so on) to Your Forecast; each writes one log line naming the
channel and the site's own address, and nothing about the visitor.
The site counts those lines by channel.

Cloudflare's [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
holds those lines, with the metadata Cloudflare attaches to each, and any error
the site's server code raises. It is set not to record each request, and keeps
every entry for at most seven days.

The same count (the channel and the site's address for each arrival, and
nothing about the visitor) is also kept in Cloudflare's
[Workers Analytics Engine](https://developers.cloudflare.com/analytics/analytics-engine/),
which deletes it after three months.

## Shared predictions

A prediction you make on [your prediction](your-forecast/) lives in its link. When
you share it, three things happen on the site's server.

- **The seal.** The page sends the prediction and its name to the server, which
  signs them with the time, using a key only the server holds, and returns the
  signature for the link to carry. Anyone opening the link can then see that
  it was sealed and when. Each seal is also kept as an entry, below.
- **The preview image.** A chat app shown the link fetches an image the server
  draws from the link. The image is kept in Cloudflare's cache, which deletes
  it on its own: an hour for an unsealed link, a year for a sealed one. Chat
  apps and search engines that fetch it may keep their own copy, under their
  own rules.
- **The count.** Shared links go out as `/s/` addresses. Each forwards to the
  prediction and writes one log line and one Analytics Engine data point naming
  "share", the button used (WhatsApp, X, copy or the phone's share menu) and
  the site's own address, as the short links above do.

## Predictions entered

Every sealed prediction is entered in a ranking against the result. Opening the
share sheet seals the prediction, and so enters it. Typing a
name or changing the prediction with the sheet open seals again, and each seal
is another entry. A person may enter several. The server stores, for each
seal, in a database at Cloudflare:

- the prediction: every ward's winner, each party's vote on the ward ballot and
  on the list ballot, and the governing parties;
- the prediction as the link carries it, and the version of the page's figures
  it was made against;
- the name you typed on it, if any;
- the time of the seal;
- the seal's id, the part of the link's `s=` after the dot;
- the model's version when it was sealed, and the version of the entry.

No IP address, browser details, cookie or account is stored with it. To limit
how often one connection can seal, the server counts seals per connection for
one minute under a scrambled form of its address, which is not stored. For an
address of the newer kind, which holds many addresses for one connection,
only its first half is used.

**Why.** To rank every prediction sealed before polls open against the result.
Until the results only the number of entries is shown. After the count the
leaderboard lists entries by place, under the name typed on each, or
"Anonymous" and the start of its seal id if none was typed. The name is then
public on the leaderboard.

**How long.** The entries are deleted ninety days after the leaderboard is
published, and within six months of polling day if no leaderboard is
published. At that deletion the names come off the leaderboard: each entry
then shows as "Anonymous" and the start of its seal id, and the leaderboard
stays on the site that way. Cloudflare keeps a recovery copy of the
database, from which deleted entries can be restored, for up to thirty days
after they are deleted.

**Removing an entry.** Write to
[psi@whysoserious.city](mailto:psi@whysoserious.city) with the link, or its
seal id. The entry is deleted from the database and, once the leaderboard is
published, from the leaderboard.

## Network error reports

Cloudflare's response headers `NEL` and `Report-To` ask your browser to report
failed connections to the site, not successful ones, to Cloudflare's
[Network Error Logging](https://developers.cloudflare.com/network-error-logging/)
service.

## What is not collected

- No accounts or sign-in. If that changes, this page changes with it.
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
only records the site keeps are those described above, held by Cloudflare for
the site; an entry is found by its seal id.

If you are not satisfied with the answer, you may complain to the
[Information Regulator](https://inforegulator.org.za/), South Africa's
regulator for POPIA.
