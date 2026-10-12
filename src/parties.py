"""Party name normalisation: many ballot spellings, one code per party.

Party names are written differently in every IEC export -- the DA is
``DEMOCRATIC ALLIANCE/DEMOKRATIESE ALLIANSIE`` in 2011 and ``DEMOCRATIC
ALLIANCE`` thereafter, COPE carries a double space, MK appears as ``M.K.`` in
by-election files -- so raw strings are folded to a canonical code before
anything is compared across elections.

Two separate ideas, deliberately kept apart:

* **Canonical code.** Every party keeps its own identity, however small. Seat
  allocation needs this: the IFP, VF+, ACDP and AIC all won CoJ seats in 2021,
  so collapsing them into an ``OTHER`` bucket would corrupt the council.
This module deliberately carries **no** grouping of parties. Which voters a
party draws on is measured per city and per election in ``src/pools.py``, so
nothing here needs to assert it, and this file stays what it should be: a
crosswalk from the many spellings on a ballot to one code per party, carrying
no knowledge of any outcome.
"""

from __future__ import annotations

import re

# `OTHER` and `INDEPENDENT` were defined here and READ BY NOTHING — deleted
# 2026-08-28 (§1.97). `OTHER` was "the residual bucket that f_other scales", and
# `f_other` was deleted on 2026-08-19 (§1.52), so it outlived its only stated
# purpose by nine days. `INDEPENDENT` was a third copy of a string the model
# reads from `seats.INDEPENDENT` (montecarlo.py imports it from there); the
# `OTHER` bucket the site shows is built in the presentation layer.

# canonical code -> (display name, has its own theta parameter)
PARTIES: dict[str, tuple[str, bool]] = {
    "ANC": ("African National Congress", True),
    "EFF": ("Economic Freedom Fighters", True),
    "MK": ("uMkhonto weSizwe", True),
    "DA": ("Democratic Alliance", True),
    "ASA": ("ActionSA", True),
    "BOSA": ("Build One South Africa", False),
    "PA": ("Patriotic Alliance", True),
    "ALJAMAAH": ("Al Jama-ah", False),
    "IND": ("Independents", False),
}

# Normalised raw string -> canonical code. Only entries that need it: anything
# not listed falls through to a code derived from the name itself.
ALIASES: dict[str, str] = {
    "AFRICAN NATIONAL CONGRESS": "ANC",
    "ECONOMIC FREEDOM FIGHTERS": "EFF",
    "UMKHONTO WESIZWE": "MK",
    "M.K.": "MK",
    "MK": "MK",
    "DEMOCRATIC ALLIANCE": "DA",
    "DEMOCRATIC ALLIANCE/DEMOKRATIESE ALLIANSIE": "DA",
    # The Democratic Party *renamed* itself the Democratic Alliance for the
    # December 2000 election, so this is continuity, not a merger, and the DP
    # appears in no election after 1999. Treating them as separate parties
    # made the DA look like a new entrant in the 1999->2000 fold.
    #
    # The New National Party and the Federal Alliance are deliberately NOT
    # mapped here even though both sat inside the DA in 2000: the NNP left in
    # 2001 and contested 2004 separately (0.81% in Johannesburg) before
    # dissolving into the ANC, so a global alias would misattribute its later
    # votes. The consequence is that the 1999->2000 fold under-credits the
    # DA's predecessor by the NNP's 3.05% and the FA's 0.50%, which is a known
    # and documented shortfall rather than a hidden one.
    "DEMOCRATIC PARTY": "DA",
    "ACTIONSA": "ASA",
    "ACTION SA": "ASA",
    "BUILD ONE SOUTH AFRICA WITH MMUSI MAIMANE": "BOSA",
    "BUILD ONE SOUTH AFRICA": "BOSA",
    "PATRIOTIC ALLIANCE": "PA",
    "AL JAMA-AH": "ALJAMAAH",
    "AL JAMA AH": "ALJAMAAH",
    "INDEPENDENT": "IND",
    "INDEPENDENTS": "IND",
}

# Parties that are not separately modelled but do win seats, so they keep stable
# codes rather than name-derived ones that could drift between elections.
MINOR_ALIASES: dict[str, str] = {
    "INKATHA FREEDOM PARTY": "IFP",
    "VRYHEIDSFRONT PLUS": "VFPLUS",
    "FREEDOM FRONT PLUS": "VFPLUS",
    "AFRICAN CHRISTIAN DEMOCRATIC PARTY": "ACDP",
    "AFRICAN INDEPENDENT CONGRESS": "AIC",
    "CONGRESS OF THE PEOPLE": "COPE",
    "UNITED DEMOCRATIC MOVEMENT": "UDM",
    "PAN AFRICANIST CONGRESS OF AZANIA": "PAC",
    "AFRICAN TRANSFORMATION MOVEMENT": "ATM",
    "AFRICAN PEOPLE'S CONVENTION": "APC",
    "AZANIAN PEOPLE'S ORGANISATION": "AZAPO",
    "NATIONAL FREEDOM PARTY": "NFP",
    "RISE MZANSI": "RISE",
    "GOOD": "GOOD",
    # Seat-winners surfaced when the crosswalk began deriving its list from
    # the IEC's own reports instead of a hand-kept Johannesburg one. Mapped
    # explicitly because a derived code can collide or drift between years.
    "UNITED INDEPENDENT MOVEMENT": "UIM",          # CoJ, 1 seat 2021
    "DEFENDERS OF THE PEOPLE": "DOP",              # Tshwane
    "REPUBLICAN CONFERENCE OF TSHWANE": "RCT",     # Tshwane
    "AGANG SOUTH AFRICA": "AGANG",
    "AFRICAN HEART CONGRESS": "AHC",
    "OPERATION KHANYISA MOVEMENT": "OKM",
    "NATIONAL COLOURED CONGRESS": "NCC",
    "OPERATION DUDULA": "DUDULA",
}


def normalise(raw: str) -> str:
    """Fold a raw party string: upper case, collapsed whitespace, tidy dashes."""
    text = (raw or "").strip().upper()
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


def _derived_code(name: str) -> str:
    """Build a stable code for a party we do not track by hand.

    Deliberately the whole name rather than initials. An earlier version built
    initials, which silently merged ``ARISE SOUTH AFRICA`` into ActionSA's
    ``ASA`` and ``ALLIED MOVEMENT FOR CHANGE`` into ``AFRICAN MOVEMENT
    CONGRESS``. These are all residual-bucket parties whose codes only need to
    be unique and stable, so verbosity costs nothing and collisions cost a lot.
    """
    code = re.sub(r"[^A-Z0-9]+", "_", name).strip("_")
    return code or "UNKNOWN"


def canonical(raw: str) -> str:
    """Return the canonical code for a raw party string."""
    name = normalise(raw)
    if name in ALIASES:
        return ALIASES[name]
    if name in MINOR_ALIASES:
        return MINOR_ALIASES[name]
    return _derived_code(name)


def display_name(code: str) -> str:
    return PARTIES.get(code, (code.replace("_", " ").title(), False))[0]


def is_modelled(code: str) -> bool:
    """True if the party carries its own theta parameter in plan §3.5."""
    return PARTIES.get(code, ("", False))[1]
