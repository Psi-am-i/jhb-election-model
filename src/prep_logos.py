"""Normalise party logos into consistent square badges.

The supplied artwork is inconsistent in a way that shows badly at small
sizes: some are line drawings on white (ANC, ACDP, FF+, Al Jama-ah), some
are full-bleed coloured tiles (ActionSA, MK, PAC, UDM, COPE), two are
transparent cut-outs (DA, IFP), and the margins differ wildly. Dropped into
a table as-is you get a solid green square next to a tiny black sketch.

This trims each to its content, re-pads it evenly on a square canvas, and
writes a fixed-size PNG, so every badge occupies the same visual weight.
Backgrounds are preserved (white stays white) and the page renders them as
rounded tiles, which reads consistently in both light and dark themes.

    python src/prep_logos.py            # -> site/logos/<CODE>.png

WHERE THESE SHOULD AND SHOULD NOT BE USED — see MODEL-LOG: logos are for
*identity* (claim boxes, candidate strips), never for *comparison* (seat
bars, coalition tables, the map key). South African party colours cluster
hard on green and gold: by dominant colour the ANC, COPE, IFP and UDM are
all yellow, and ActionSA, ATM, PAC, FF+, Al Jama-ah and MK are all green.
The abstract chips exist precisely because they can be told apart.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

# artwork filename -> our party code
CODES = {
    "ANC": "ANC", "DA": "DA", "actionSA": "ASA", "mk": "MK",
    "Inkatha": "IFP", "FF+": "VFPLUS", "ACDP": "ACDP",
    "Al-Jama-ah": "ALJAMAAH", "ATM": "ATM", "COPE": "COPE",
    "PAC": "PAC", "UDM": "UDM",
}

# modelled individually but with no artwork supplied
MISSING = ["EFF", "PA", "RISE", "BOSA"]


def content_box(im: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box of the logo itself, ignoring transparent or white margin."""
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    box = alpha.getbbox() if alpha.getextrema()[0] < 250 else None
    if box:
        return box
    grey = rgba.convert("L")
    # anything not near-white counts as content
    mask = grey.point(lambda v: 255 if v < 245 else 0)
    return mask.getbbox() or (0, 0, im.width, im.height)


def normalise(src: Path, size: int, pad: float) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    left, top, right, bottom = content_box(im)
    logo = im.crop((left, top, right, bottom))

    # the background to keep: transparent stays transparent, otherwise the
    # artwork's own corner colour (white tile or brand tile)
    corner = im.getpixel((1, 1))
    bg = (0, 0, 0, 0) if corner[3] < 40 else corner

    side = max(logo.width, logo.height)
    canvas_side = int(side * (1 + pad * 2))
    canvas = Image.new("RGBA", (canvas_side, canvas_side), bg)
    canvas.paste(logo, ((canvas_side - logo.width) // 2,
                        (canvas_side - logo.height) // 2), logo)
    return canvas.resize((size, size), Image.LANCZOS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=Path("party_logos"))
    ap.add_argument("--out", type=Path, default=Path("site/logos"))
    ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--pad", type=float, default=0.10,
                    help="margin as a fraction of the logo's long side")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    written = []
    for src in sorted(args.src.glob("*.png")):
        code = CODES.get(src.stem)
        if code is None:
            print(f"  ? {src.name}: no party code mapped, skipped")
            continue
        out = args.out / f"{code}.png"
        normalise(src, args.size, args.pad).save(out, optimize=True)
        written.append(code)
        print(f"  {code:9s} <- {src.name:16s} {out.stat().st_size / 1024:5.1f} kB")

    print(f"\n{len(written)} badges at {args.size}px -> {args.out}")
    if MISSING:
        print("no artwork supplied for: " + ", ".join(MISSING)
              + "\n  -> these parties fall back to their colour chip, so do NOT"
                "\n     use logos anywhere every party must appear.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
