# Home page introduction: draft for the owner (item 5)

Edited from the owner's words to STYLE.md. `{{…}}` marks a figure filled from
where it is generated; none is typed.

**The 34%.** It exists: it is `backtest_crps_better`, "how much lower the
model's distributional error is" than the toughest simple baseline, on the
methodology page. It is not "beats baselines by 34%" in general. The seat
error is `backtest_seat_err_model` against `backtest_seat_err_baseline`
seats misallocated (today 297 against 353), and the model beats the toughest
baseline in `backtest_wins` of `backtest_cities` cities (today 7 of 8). The
draft says which comparison the 34% is.

---

**What this is**

An unaffiliated forecast of Johannesburg's council election, built from primary
sources. It starts from each voting district's history: past results, turnout,
census data and each party's trajectory. From there it builds the city up from
its wards, rather than applying generalisations down.

The model simulates the election thousands of times. In each run, turnout and
every party's support differ, within the ranges history has shown. The
forecast is how often each outcome happens. You can pick an outcome and see
what had to happen in the simulations where it occurred.

It uses no opinion polls. Tested on past elections in cities it was not built
for, its forecasts score {{backtest_crps_better}} better than the best simple
baseline, measured on the full spread of outcomes. It misallocates
{{backtest_seat_err_model}} seats where the baseline misallocates
{{backtest_seat_err_baseline}}, and it beats that baseline in {{backtest_wins}}
of {{backtest_cities}} cities.

It uses as few judgement calls as possible. Each one is declared, and each can
be changed. It works this way because a forecast derived from history can be
applied anywhere, then adjusted by people who know a particular election in a
particular place.
