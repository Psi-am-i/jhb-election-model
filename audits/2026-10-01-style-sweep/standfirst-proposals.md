# STYLE.md rule 9 on frozen text — proposals for the owner

Rule 9: a standfirst never restates the first paragraph, and every sentence has
a subject and a verb. The texts below are dated, published pieces (the 8 August
article and the 6 August review), so none of this is applied. Each block is
before/after. No figure is changed; the only typed figures involved are the
historical ones already in the "before" text.

If approved: paste each "after" over its field and decide whether the change
needs a dated note (the convention for a published piece).

---

## Article teasers on the home page (`content/joburg/articles.toml`)

Present in the live 8 August build (`archive/live-deployed-2026-08-08/index.html`).

### "Nobody will win Johannesburg — …" (lead)

Restates the first paragraphs of "Wards, lists — and the November surprise",
which open the article.

Before:

> Johannesburg votes on two ballots at once, and they are added together. A
> party with tightly concentrated support can win more wards than its share
> entitles it to — and nobody unseats a ward winner. The shortfall is taken from
> every other party. The clause has fired exactly once before, in a Karoo town of
> seven seats.

After:

> A rarely used clause lets a party keep every ward it wins beyond its share of
> the vote. The shortfall is taken from every other party. It has fired once
> before, in a Karoo town of seven seats.

### "When the ANC falls, nobody catches the votes"

Restates the section's first paragraph ("The opposition captured essentially
none of them").

Before:

> The opposition captured essentially none of the 587,000 votes the ANC bloc
> shed between the 2019 national election and the 2021 local election. The
> city's collapse in ANC support did not become anybody else's gain — it became
> abstention.

After:

> Between the 2019 national election and the 2021 local election, voters who
> left the ANC stayed home. The opposition's share rose because the total
> shrank.

Note: the "after" drops the 587,000 figure from the teaser rather than move it;
the article carries it as `{{bloc_leak_votes}}`.

### "If the law were German instead"

No main verb.

Before:

> The same votes under our seat law and Germany's of 2000, 2015 and 2023.

After:

> The same votes are counted under our seat law and under Germany's of 2000,
> 2015 and 2023.

### "Laingsburg, 2021"

No main verb; restates the section heading ("the whole mechanism in seven
seats") and its first sentence ("it has fired exactly once").

Before:

> The only place the clause has fired — the whole mechanism in a council of
> seven.

After:

> The clause has fired once, in a council of seven. The Electoral Commission's
> calculation shows each step.

---

## "Nobody will win Johannesburg" (`forecast-sheet.html`, `__ARTICLE_ONLY__`)

### Article standfirst and the first section

The standfirst's second sentence ("A rarely-used clause … will hand the
shrinking ANC an unbreakable floor … the shortfall will be taken from every
other party") is restated by the second paragraph of "Wards, lists — and the
November surprise" ("Its ward count is an unbreakable floor — and the parties
squeezed to pay for it are everyone else"). Proposal: cut the closing clause of
that paragraph.

Before:

> … in {{pub0831_p_excessive_anc}} of simulations. Its ward count is an
> unbreakable floor — and the parties squeezed to pay for it are everyone else.

After:

> … in {{pub0831_p_excessive_anc}} of simulations.

No token moves.

### "Other Proportional Representation Mechanisms"

The eyebrow, heading and the home teaser all introduce the same comparison; the
section has no standfirst of its own, so rule 9 does not bite. No proposal.

---

## The review (`docs-public/review.md`, published 6 August 2026)

The site-chrome standfirst ("Six implementation errors found by a hostile read
of the model's own plan, one of which made the first forecast's headline claim
false, and what each repair changed.") restated the first paragraph and was
removed. A non-overlapping standfirst was considered; the first paragraph and
the since box already say everything one could carry. The body is frozen and
has no proposal here; `review-proposals.md` holds the earlier ones.
