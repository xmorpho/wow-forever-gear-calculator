# WoW: Forever Gear Comparator V2.4 — Inventory icon patch

Official project website: https://xmorpho.github.io/wow-forever-gear-calculator/

**Source credit:** Item data and embedded tooltip/icon data by [ForeverDB.net](https://foreverdb.net). Game artwork © Blizzard Entertainment; this is an unofficial fan project by Morph.

## What changed

- Restores **real WoW inventory icons**, not drawings, emojis or models. If the local ForeverDB catalog includes a valid icon filename, the UI loads it as a full-size image. If only a ForeverDB item ID is known, the official ForeverDB icon-enabled embed provides the icon. No alternate icon is invented.
- Adds an explicit `ForeverDBTooltips.refresh()` call for dynamically rendered search results, selected items and saved gear, including on the external script's load event. This was missing in V2.3.
- Fits a rendered icon to the existing 60/50/44-pixel tile without stretching the item panel, and hides the fallback character once the real icon is loaded.
- Uses Azure Silk Hood (#7048, `inv_helmet_29`) as the named regression test; its +10 Frost Damage bonus is retained in estimated-mode calculations, with armor and other effects displayed as in the V2.4 preview.
- Leaves all ForeverDB updater/automation files **unchanged**. There is no API refresh needed for this patch.

## How to publish

1. GitHub Desktop: Fetch/Pull origin.
2. Back up your current `index.html` and `README.md` if you want a local rollback copy.
3. Replace **only** `index.html` and `README.md` in the repository root with these files. Do **not** delete or modify `data/foreverdb-items.json`, `.github/`, or `scripts/`.
4. Commit and push; after a green Pages deployment check, force refresh the site (Ctrl+Shift+R).
5. Test Azure Silk Hood (`7048`) in Current Gear and New Gear, plus a second item with an available catalog icon. Check the icon, armor and Frost Damage note.

The icon loading integration was tested against a simulated ForeverDB script in a local browser, including DOM injection and layout sizing. The actual third-party icon response cannot be exercised from the offline test environment; please verify on your live published website. The version 2.4 tooltip stat improvements use local tests and do not modify the 8,500 cached records.
