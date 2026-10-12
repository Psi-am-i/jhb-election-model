# Poll research — what exists for Johannesburg 2026, and each house's record

Commissioned 2026-09-24 (Scout session) because the owner asked, on the
interactive's poll control: *"Why do we only have a single poll? Are there more
polls? Do we have known errors per polling house?"* Web research by a read-only
agent; the Ipsos 2026 Johannesburg row was **re-derived by the lead from the
primary PDF** (`sources/ipsos-2026-09-04-key-metros-charts.pdf` p.8 and
`…-release.pdf`). Everything else is as the agent reported it and is marked
primary or secondary. **Nothing here has entered `polls.json`**; admitting any
of it is a register change and goes through `polling.screen`.

## 1. What exists for Johannesburg 2026

| house / sponsor | fieldwork | n | figures as published | status |
|---|---|---|---|---|
| SRF + The Common Sense, fieldwork Victory Research | 16 Feb – 6 Mar 2026 | ~500 | DA 39, ANC 30, ASA 10, MK 8, EFF 4 | in register, admitted |
| SRF + The Common Sense, Victory Research | 8 – 31 Jul 2026 | 504 | DA 42, ANC 18, MK 13, ASA 10, EFF 8 (53% turnout model) | in register, admitted |
| **Ipsos Khayabus "Pulse of the People"** (own omnibus), released 4 Sep 2026 | **June – July 2026** | 3,600 national; JHB cut unpublished, **±5.57 max MoE ⇒ n ≈ 310** (inferred, SRS) | **ANC 31, DA 28, ASA 14, EFF 8, MK 6, PA 3, Other 7, DK 3** — among those expressing a preference; the 17% "will not vote" excluded | ⛔ **NOT in register.** Verified by the lead from the primary PDF |
| DA internal, via Zille / News24 | reported 1 Aug 2026 | none | DA 40, ANC 27 (search summary only; paywalled) | in register, declined (commissioned) |
| DA internal | late Aug 2025 | none | DA 37, ANC 31 (Daily Maverick) | not in register |

⚠️ **Two corrections to what circulated in the 24 Sep round:** the Ipsos poll
is **June–July fieldwork**, not September (September is the release), and the
DA figure is **28**, not 27 (Daily Maverick's report is wrong).

⚠️ **Independence of SRF is contested, unverified:** IOL (2026-08-23) reports
Gareth van Onselen, a former DA staffer, behind The Common Sense. Not checked.

Nothing found for 2026 Johannesburg from Citizen Surveys, Market Research
Africa, Afrobarometer or any university. The Brenthurst Foundation closed
(16 Jul 2025).

## 2. Scored record per house (decided shares vs valid votes; poll − actual, pp)

Agent's arithmetic; several inputs secondary — **re-derive before any of these
becomes a constant.**

| house | readings | party-errors | RMS | local-election record? |
|---|---|---|---|---|
| Ipsos | 7 (2016 LGE nat + JHB/TSH/NMB, 2019 nat, 2021 LGE nat, 2024 nat) | 28 | 2.84 | **yes** — LGE-only RMS 2.48 (18 errors); 2016 metros RMS 2.63 |
| SRF (daily tracker) | 1 (2024 nat) | 5 | 1.48 (1.30 on an alternative transcription) | **no** |
| IRR / Victory (SRF's lineage) | 2 (2019 nat, 2019 GP) | 5 | 3.74 | no |
| Victory for Media24 | 1 (2021 LGE nat) | 3 | 5.45 — ANC +9.4 | national LGE only |
| Afrobarometer / AtlasIntel / Markdata / Brenthurst | 1 each (2024 nat) | 4–5 | 2.76 / 1.62 / 2.24 / 2.79 | no |

⚠️ The 2016 Ipsos metro errors here (JHB ANC +1.08, DA +2.52, EFF −2.93 against
the PR ballot) differ from the nine readings `polling.py` records as
`POLL_RMS_ERROR_2016`'s provenance (JHB 1.4 / 2.6 / 3.1). For Johannesburg
the gap is the actuals basis: against the COMBINED ballot the agent reports
(44.50 / 38.41 / 11.09) the errors are 1.5 / 2.6 / 3.1, i.e. `polling.py`
scored against combined. Nelson Mandela Bay differs more (agent 0.2 / 1.7 / 1.5
after removing 9% undetermined; `polling.py` 3.9 / 2.7 / 0.9) and is
**unresolved — check before touching that constant.**

**The finding that matters for the design:** Ipsos is the only house with a
scored Johannesburg reading (2016). SRF — the only house admitted at 2026 —
has **no** scored local-election reading, and its lineage's one LGE reading
missed the ANC by 9.4pp.

## Sources

Primary PDFs in `sources/`. URLs as the agent gave them:
- Ipsos 2026: ipsos.com/sites/default/files/ct/news/documents/2026-09/ (Key metros remain battlegrounds … 4 September 2026)
- SRF: thecommonsense.co.za/politics/anc-support-collapses-johannesburg ; thecommonsense.co.za/polls/support-political-parties-johannesburg
- DA internal: news24.com/politics/internal-polls-show-da-leading-in-johannesburg-says-helen-zille-20260801-0799 ; dailymaverick.co.za/article/2025-10-01-da-ahead-of-anc-in-internal-party-polls-…
- Ipsos 2016: ipsos.com/en-za/elections-2016-poll-polls ; ipsos.com/en-za/ipsos-pre-election-forecasting-mark-nationally
- Ipsos 2021: news24.com/southafrica/news/ancs-support-in-municipal-elections-below-50-ipsos-poll-predicts-20211031
- IRR 2019: irr.org.za/reports/criterion-report/files/thecriterionreportv2n3-april2019.pdf ; businesstech.co.za/news/government/315202/
- IOL on SRF: iol.co.za/news/politics/2026-08-23-anc-at-18-former-da-man-gareth-van-onselens-hidden-hand-behind-the-polls/
- Everything else: Wikipedia opinion-polling pages for 2019/2024 general and 2016/2021 municipal elections (secondary).
