"""Party name normalisation and the bloc structure the model draws on.

Party names are written differently in every IEC export -- the DA is
``DEMOCRATIC ALLIANCE/DEMOKRATIESE ALLIANSIE`` in 2011 and ``DEMOCRATIC
ALLIANCE`` thereafter, COPE carries a double space, MK appears as ``M.K.`` in
by-election files -- so raw strings are folded to a canonical code before
anything is compared across elections.

Two separate ideas, deliberately kept apart:

* **Canonical code.** Every party keeps its own identity, however small. Seat
  allocation needs this: the IFP, VF+, ACDP and AIC all won CoJ seats in 2021,
  so collapsing them into an ``OTHER`` bucket would corrupt the council.
* **Bloc.** The modelling grouping from plan §3.4(a)/§3.5. Swings are drawn at
  bloc level and split within the bloc, so a party's bloc decides which Δ it
  moves with. ``OTHER`` here means "not separately modelled", not "discarded".

Rev 2 of the plan promoted the PA and Al Jama-ah out of ``OTHER`` into blocs of
their own, and gives θ parameters to the ANC, DA, EFF, ActionSA, MK and PA.
"""

from __future__ import annotations

import re

# Bloc labels. ANC/DA blocs move together under Δ_ANCbloc and Δ_DAbloc; the PA
# and Al Jama-ah are modelled individually; OTHER is the residual bucket that
# f_other scales.
ANC_BLOC = "ANC_BLOC"
DA_BLOC = "DA_BLOC"
OTHER = "OTHER"
INDEPENDENT = "INDEPENDENT"

# canonical code -> (display name, bloc, has its own theta parameter)
PARTIES: dict[str, tuple[str, str, bool]] = {
    "ANC": ("African National Congress", ANC_BLOC, True),
    "EFF": ("Economic Freedom Fighters", ANC_BLOC, True),
    "MK": ("uMkhonto weSizwe", ANC_BLOC, True),
    "DA": ("Democratic Alliance", DA_BLOC, True),
    "ASA": ("ActionSA", DA_BLOC, True),
    "BOSA": ("Build One South Africa", DA_BLOC, False),
    "PA": ("Patriotic Alliance", "PA", True),
    "ALJAMAAH": ("Al Jama-ah", "ALJAMAAH", False),
    "IND": ("Independents", INDEPENDENT, False),
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


def bloc(code: str) -> str:
    """Return the modelling bloc for a canonical code."""
    return PARTIES.get(code, ("", OTHER, False))[1]


def display_name(code: str) -> str:
    return PARTIES.get(code, (code.replace("_", " ").title(), OTHER, False))[0]


def is_modelled(code: str) -> bool:
    """True if the party carries its own theta parameter in plan §3.5."""
    return PARTIES.get(code, ("", OTHER, False))[2]
