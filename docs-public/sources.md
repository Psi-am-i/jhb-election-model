# Where the data comes from

The technical recipes, file by file, are in
[`SOURCES.md` on GitHub](https://github.com/Psi-am-i/jhb-election-model/blob/main/SOURCES.md).

## Public records that are hard to reach

The IEC's results sites, `results.elections.org.za` and `www.elections.org.za`,
refuse automated requests. Election results are public records, and no reason
for the restriction is given. Most of the raw data behind this model was
collected through an ordinary browser session, one file at a time.

The portal identifies each election by an internal code, not by its year, and
the national and provincial halves of the same election day have different
codes. A wrong guess raises no error: the site returns a different election's
results. One election, the 2014 national and provincial vote, is missing from
the results portal; its files are on a second, older IEC site.

## The election results

The model rests on six elections at voting-district level, the finest grain the
IEC publishes:

| Election | What it provides |
|---|---|
| 2011, 2016, 2021 municipal elections | Both ballots — ward and party list — for every voting district |
| 2014, 2019, 2024 national/provincial elections | The provincial ballot, the model's between-elections baseline |

The files were not clean. Different years arrive in different character
encodings, one from the DOS era. A voting station with a comma in its name
shifts every later column in the row. One year's "valid votes" column does not
contain what its name says. None of these raises an error; each was caught by
cross-checking totals against the IEC's own published reports. The full list,
and the code that handles each, is on GitHub.

## The maps

Council seats follow geography, so the model needs the boundaries of every ward
and voting district across four boundary revisions: Johannesburg's wards have
been redrawn before every election. The Municipal Demarcation Board publishes
the recent layers through its mapping portal; the two older ward sets survive
only as archived file downloads.

The Demarcation Board has retired the per-municipality downloads its old website
offered. One dataset this model needed, the complete voting-district results of
the 2016 election, now exists in the Internet Archive and nowhere official.

The 2026 voting-district layer carries a field that looks like current voter
registration. It is a snapshot from 2024. Every turnout figure built on it as
current would be wrong.

## By-elections

Fifteen Johannesburg wards have held by-elections since 2021. They are the only
direct evidence of how opinion has moved between elections. The model reads them
and, in this forecast, gives them no weight (see the methodology). The IEC's official download page could not supply them: its report
links work only inside the browser session that created them. The IEC's public
dashboard is fed by plain data files that anyone can read, with more detail than
the reports, down to voting-district level with every party and candidate. The
model uses those.

## People

Statistics South Africa publishes ward-level population estimates from Census
2022 (age, sex and population group for all 135 wards), and the turnout
modelling uses them. The more detailed small-area data (income, dwelling type,
employment) is not published, because at ward level it can identify households.
Access under conditions exists, and we have not sought it.

## What nobody publishes

- **Historic voting-district boundaries.** The IEC draws these with its own
  mapping systems and appears never to have published them. Five archives and
  catalogues were searched; a request to the IEC's Delimitation Directorate is
  the remaining route. The model works around the gap and tests that the
  workaround does not change its conclusions.
- **The voters' roll by age and sex below municipality level**, and the
  registration figures from the 2026 sign-up weekends, which are not released
  yet.

## Checksums

The raw files were assembled by hand from sources that can change or vanish, so
the build records a cryptographic checksum of each file when it is collected: a
short code that changes if one byte of the file does. The checksums, and the
instructions to fetch each file, are published in the project's repository on
[GitHub](https://github.com/Psi-am-i/jhb-election-model); the raw files are too
large to publish. Anyone who downloads the same sources can confirm they hold
exactly the data this forecast was computed from, and a file altered or
withdrawn upstream shows up as a mismatch.
