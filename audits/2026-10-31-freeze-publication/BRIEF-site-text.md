# Brief: publish the freeze hash, the inputs and the preflight check (for owner approval)

**Due:** 31 October (PLAN.md 5.1). **Owner approval needed for every word below**
(QC.md §4b; no reader words outside an approved brief).

## What changes on the site

1. **Four files served as they are**, under `/freeze/`:
   - `/freeze/forecast_frozen.json` (the freeze, 5,000 simulations)
   - `/freeze/inputs.json` (151 input files with their sha256)
   - `/freeze/preflight.txt` (the input check's output)
   - `/freeze/scoring.json` (the commit and sha256 of the files that will score every forecast after the election)
   Build change: `build_site.py` copies them from `audits/2026-10-31-freeze-publication/`; `_headers` gets a rule for `/freeze/*` (JSON and plain text).

2. **One new section on /methodology**, placed after the last section, heading and text:

> ### The frozen forecast
>
> The forecast was fixed on 24 October 2026, before any votes were cast. Its fingerprint is
>
> `10bdccc05423b0db38b0a52aeb8d6bd192539442e75da113ee07bc224ebc7c4a`
>
> a sha256 hash of the 5,000 simulations and every setting that produced them. Re-running the model from the same code and inputs gives the same hash; any change to a setting, an input or a single simulation gives a different one.
>
> - [The frozen forecast](/freeze/forecast_frozen.json)
> - [Every input file it read, with its own hash](/freeze/inputs.json) (151 files)
> - [The input check run before freezing](/freeze/preflight.txt). It flags one input: the voters' roll is the IEC's 26 September figure, which matched the IEC's latest published roll, dated 29 September, in all 135 wards on 28 October.
>
> **How forecasts will be scored.** Every forecast on this site, ours and readers', will be scored by the same code after the election: seats first, then wards called correctly, then the list vote. That code was fixed on 31 October; its fingerprint is [here](/freeze/scoring.json).

3. **/changes** gets nothing new (the forecast did not change).

## Questions for the owner

- **Approve the words above, or edit them.**
- **Replace `data/processed/forecast_frozen.json`** (the 1,500-simulation freeze, `e1b960fb…`) with the 5,000-simulation one? It is what the page would publish; until then the repository holds both.
- **The code these hashes refer to is not public yet** (`site-sweep-1` is not on GitHub; the history scan is open). Readers can check the forecast hash only by asking for the code. Push before or after publishing?
- **Promotion:** after approval I build and upload a UAT version and check it; going live is yours.
