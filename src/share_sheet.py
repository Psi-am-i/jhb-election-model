"""THE ONE SHARE SHEET's markup (owner, 2026-10-11: one sheet, reused).

Every share sheet the site serves is written here: the one by each page's
title (``build_site.share_button``) and the two on "Your forecast"
(``build_your_forecast.assemble``, at its ``<!-- __YFSHEET:<name>__ -->``
markers). Its controls are ``src/js/share-dialog.js`` and its look
``src/css/share-sheet.css``; the classes below are the ones both read.

What differs between the sheets is content only, passed in: the heading, the
link's label, the image the preview starts with, and the blocks "Your
forecast" adds (the name above the link; the seal, the entry note and the
image picker below it).
"""
from __future__ import annotations

from html import escape

#: The dialog's class (share-sheet.css; not ``sheet``, the forecast pages'
#: column).
DIALOG_CLASS = "sharesheet"


def sheet(*, heading_id: str, heading: str, link_label: str, native: str = "primary",
          above_link: str = "", below_link: str = "", img_src: str = "", img_alt: str = "",
          ready: bool = False, indent: str = "") -> str:
    """The ``<dialog>`` of a share sheet.

    ``heading_id`` names its heading (the dialog's accessible name);
    ``native`` is the Share… button's look (``primary``, the reader's colour,
    or ``model``, the model's accent); ``above_link`` and ``below_link`` are
    markup a caller adds around the link; ``img_src``/``img_alt`` the image
    the preview starts with (none: the caller draws one); ``ready`` leaves
    Share… and Download image enabled from the start (a sheet whose image is
    a file), where a sheet that draws its image enables them once drawn.
    ``indent`` is prefixed to every line after the first."""
    off = "" if ready else " disabled"
    img = (f'<img src="{escape(img_src)}" alt="{escape(img_alt)}" loading="lazy">' if img_src
           else f'<img alt="{escape(img_alt)}">')
    lines = [
        f'<dialog class="{DIALOG_CLASS}" aria-labelledby="{heading_id}">',
        f'  <div class="dh"><h2 id="{heading_id}">{escape(heading, quote=False)}</h2>',
        '    <button class="x" type="button" aria-label="Close">×</button></div>',
        '  <div class="db">',
        *([f"    {above_link}"] if above_link else []),
        '    <div class="urlrow">',
        f'      <input class="shurl" type="text" readonly value="" aria-label="{escape(link_label)}">',
        '      <button class="btn shcopy" type="button">Copy link</button>',
        '    </div>',
        *([f"    {below_link}"] if below_link else []),
        f'    <div class="preview">{img}</div>',
        '    <div class="shcta">',
        f'      <button class="btn {native} shnative" type="button" hidden{off}>Share…</button>',
        '      <a class="btn shwa" target="_blank" rel="noopener">WhatsApp</a>',
        '      <a class="btn shx" target="_blank" rel="noopener">X</a>',
        f'      <button class="btn shdl" type="button"{off}>Download image</button>',
        '    </div>',
        '    <p class="toast" role="status" aria-live="polite"></p>',
        '  </div>',
        '</dialog>',
    ]
    return ("\n" + indent).join(lines)
