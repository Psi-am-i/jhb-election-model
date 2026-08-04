# Where the data comes from — and what it took to get it

Every number in this model traces back to a public record: election results,
maps of voting districts and wards, by-election returns, census tables. This
page says where each one lives, what state it was in when we found it, and —
because it turned out to matter — how hard South Africa's public records
actually are to reach. The full technical recipes, file by file, are in
[`SOURCES.md` on GitHub](https://github.com/Psi-am-i/jhb-election-model/blob/main/SOURCES.md).

## Public records, deliberately hard to reach

The IEC's results sites — `results.elections.org.za` and
`www.elections.org.za` — do not allow programmatic collection of their data:
automated requests are simply refused at the door. Why that should be true of
a public record is unexplained. Election results belong to everyone, and they
should be freely and easily available — not guarded in ways that make
independent analysis a test of patience. In practice, most of the raw data
behind this model had to be collected through an ordinary browser session,
clicking each file one by one.

It gets stranger. The portal identifies each election not by its year but by
an arbitrary internal code — and the codes for the national and provincial
halves of the same election day differ. Guess wrong and the site does not
error: it quietly hands you a different election's results. And one election —
the 2014 national and provincial vote — is missing from the results portal
altogether; its files turned out to live on a second, older IEC site.

## The election results themselves

The model rests on six elections at voting-district level — the finest grain
the IEC publishes:

| Election | What it provides |
|---|---|
| 2011, 2016, 2021 municipal elections | Both ballots — ward and party list — for every voting district |
| 2014, 2019, 2024 national/provincial elections | The provincial ballot, the model's between-elections baseline |

The files themselves were not clean. Different years arrive in different
character encodings — one in a format from the DOS era. A voting station with
a comma in its name silently shifts every later column in the row. One year's
"valid votes" column does not contain what its name says. Each of these
corrupts results without raising any error; each had to be caught by
cross-checking totals against the IEC's own published reports. The full list
of traps, and the code that handles them, is on GitHub.

## The maps

Council seats follow geography, so the model needs the boundaries of every
ward and voting district — across four different boundary revisions, because
Johannesburg's wards have been redrawn before every election. The Municipal
Demarcation Board publishes the recent layers through its mapping portal; the
two older ward sets survive only as archived file downloads.

Public geodata also quietly disappears: the Demarcation Board has already
retired the per-municipality downloads its old website offered. One dataset
this model needed — the complete voting-district results of the 2016
election — now exists in the Internet Archive and nowhere official.

One trap worth recording: the 2026 voting-district layer carries a field that
looks like current voter registration. It is actually a snapshot from 2024.
Take it at face value and every turnout figure built on it is wrong.

## By-elections

Fifteen wards in Johannesburg have held by-elections since 2021 — the only
hard evidence of how opinion has moved between elections, and an input to this
forecast. The IEC's official download page could not supply them: its report
links only work inside the browser session that created them. The IEC's own
public dashboard, however, is fed by plain data files that anyone can read —
richer than the reports, down to voting-district level with every party and
candidate. That is what the model uses.

## People

Statistics South Africa publishes ward-level population estimates from Census
2022 — age, sex and population group for all 135 wards — and those are used in
the turnout modelling. The more detailed small-area data (income, dwelling
type, employment) is not published at all: it is supplied on request, by
email, to those who know to ask. A national census, funded publicly, should
not work that way.

## What nobody publishes

Some records could not be obtained because they do not exist in public:

- **Historic voting-district boundaries.** The IEC draws these with its own
  mapping systems and appears never to have published them. Five archives and
  catalogues were searched; a request to the IEC's Delimitation Directorate is
  the only remaining route. The model works around the gap and tests that the
  workaround does not change its conclusions.
- **The voters' roll by age and sex below municipality level**, and the
  registration figures from the 2026 sign-up weekends — the latter simply not
  released yet.

## Keeping ourselves honest

Because the raw files were assembled by hand from unreliable sources, every
one of them is fingerprinted: a cryptographic checksum of each input is
recorded in the public repository, so anyone rebuilding this model can prove
they are working from byte-identical data — and we will know immediately if a
source file quietly changes underneath us.
