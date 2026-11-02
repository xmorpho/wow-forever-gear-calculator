# WoW: Forever Gear Comparison Calculator

An unofficial, fan-made equipment comparison tool for **World of Warcraft: Forever**. Compare two items for any of the game's nine classes, select a specialization and playstyle, and adjust estimated stat weights.

## Play online

Once GitHub Pages is enabled, open the website shown under **Settings → Pages**.

## Features

- Side-by-side item comparison with editable tooltip stats
- Nine playable classes and their specialization options
- Estimated Mode (editable, **not authoritative** stat weights) and Verified Mode (no numeric score if required combat formulas are unknown)
- Searchable starter item catalog, manual item creation, and JSON import/export
- Optional ForeverDB API-assisted catalog refresh, subject to approval, CORS/network access, and rate limits

## Data credit

**Item data from [ForeverDB.net](https://foreverdb.net).** ForeverDB provides the source item data; this calculator is an independent fan project. Original item data may change between client builds; in-game tooltips take precedence.

## Important limitations

The starter catalog is not the entire ForeverDB inventory. Loading additional data directly in your browser is *not* the same as publishing that catalog to all visitors. Estimated item scores are comparisons of user-configured weights, not verified DPS, healing, threat, or survival predictions. No API credentials should be committed to this public repository or placed in `index.html`.

## Disclaimer

Not affiliated with, endorsed by, or sponsored by Blizzard Entertainment or ForeverDB.
