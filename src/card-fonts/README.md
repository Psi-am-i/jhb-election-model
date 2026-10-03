# Fonts for the share cards rendered at the edge

TrueType copies of five of the site's own IBM Plex faces (`src/fonts/`, the
Latin-1 subsets the site serves as WOFF2), for `src/og-render.js`: resvg, which
draws the link preview of a shared forecast, reads TrueType or OpenType only.
`interactive/js/card-fonts.js` holds their advance widths
(`interactive/tools/card_fonts.mjs`), so the card is measured with the faces
that draw it. Licence: SIL Open Font License 1.1, `OFL.txt` (the same file as
`src/fonts/OFL.txt`).

| file | from |
|---|---|
| `IBMPlexSans-Regular-Latin1.ttf` | `src/fonts/IBMPlexSans-Regular-Latin1.woff2` |
| `IBMPlexSans-SemiBold-Latin1.ttf` | `src/fonts/IBMPlexSans-SemiBold-Latin1.woff2` |
| `IBMPlexSans-Bold-Latin1.ttf` | `src/fonts/IBMPlexSans-Bold-Latin1.woff2` |
| `IBMPlexSerif-SemiBold-Latin1.ttf` | `src/fonts/IBMPlexSerif-SemiBold-Latin1.woff2` |
| `IBMPlexMono-SemiBold-Latin1.ttf` | `src/fonts/IBMPlexMono-SemiBold-Latin1.woff2` |

Converted on 3 October 2026 with fontTools 4.66.1 and brotli 1.2.0 (a scratch
virtualenv; the project's `.venv` carries neither), unchanged but for the
container:

    python -c "import sys; from fontTools.ttLib import TTFont; \
      f = TTFont(sys.argv[1]); f.flavor = None; f.save(sys.argv[2])" \
      src/fonts/<face>-Latin1.woff2 src/card-fonts/<face>-Latin1.ttf

A name with a character outside Latin-1 and the subsets' punctuation has no
glyph in these files; the card measures such a character as the face's widest
glyph and resvg draws nothing for it.
