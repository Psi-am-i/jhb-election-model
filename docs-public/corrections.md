# Corrections

A **correction** means the page was wrong when it was published. That is different from an **update**, where the
model or the world moved and the earlier statement was true on its date;
updates appear beside the original as a dated "what the model says now" box.

Nothing is removed from this list.

<span data-asof="2026-09-17">

## 17 September 2026 — the headline figures disagreed with the article beside them

**What we published.** On the front page from 31 August, the summary tiles said
the DA was the largest party in **62%** of simulations, that the ANC triggered
the excessive-seats clause in **96%**, and that the ANC and DA together had a
majority in **88%**. The article immediately below them, drawing on the same
forecast, said **71%**, **58%** and **58%**.

**What was true.** The article's figures. The tiles were left over from an
earlier model run.

**How it happened.** The tiles were written into the page by a script when a
reader opened it, from a block of numbers pasted into the page. Everything else
came from the build, which checks each figure against the current run. Nothing
compared the two, so the page could disagree with itself and no check noticed.

**What changed.** Every figure on the site is now written at build time and
carries its source, and the build refuses to publish a page whose scripts could
write a figure. The tiles now show their own history: hovering one gives what it
says today and what it said on 31 August.

</span>

<span data-asof="2026-09-17">

## 17 September 2026 — the ANC's list seats were shown as 7

**What we published.** The "two ballots" bars showed the ANC taking **7** list
seats, next to a tile saying the excessive-seats clause fires in most
simulations — which means it takes **none**.

**What was true.** In 64% of simulations the ANC gets no list seats at all. In
the rest it gets about nine.

**How it happened.** The bar subtracted the ANC's average ward wins from its
median total seats. Mixing an average and a median like that produces a number
no simulation ever produced.

**What changed.** The three bars now show one real simulation — the one closest
to every party's median — so they add up and agree with the tile beside them.

</span>

<span data-asof="2026-09-17">

## 17 September 2026 — "smaller parties" was shown as 39 seats

**What we published.** The council bar gave smaller parties **39** of 270 seats.

**What was true.** About 25 on average. Parties outside the named ones won 16
seats in 2011, 13 in 2016 and 24 in 2021.

**How it happened.** The bar filled the gap left after subtracting each named
party's median from 270. Medians do not add up: the parties' medians together
came to 240, so the leftover absorbed 30 seats belonging to nobody.

**What changed.** The same fix as above: one real simulation, which adds up.

</span>
