# ⚔ WoW: Forever Gear Comparator — V2.1

**Made by Morph.** A free, unofficial gear companion for World of Warcraft: Forever. **Should I equip this new item?** Search for equipment, compare actual available tooltip attributes, and see an Equip / Keep / Too Close to Call recommendation based on your selected class and playstyle.

**Live website:** https://xmorpho.github.io/wow-forever-gear-calculator/

## Data credits

**Item data and embedded item tooltips are provided by [ForeverDB.net](https://foreverdb.net).** The application retains a visible source link alongside its item catalog and in its footer. Please retain that visible credit in future versions. ForeverDB's [developer rules](https://foreverdb.net/developers) require source attribution wherever its data is displayed. The official [tooltip integration](https://foreverdb.net/embed) is also included. WoW game assets belong to their respective owners. This website is not affiliated with Blizzard or ForeverDB.

## What's new in V2.1

- **Click any empty or occupied character equipment slot** to open an item picker. Search within that slot, select an existing ForeverDB item, or enter a custom item name and the stats on your tooltip. Saved gear stays in your own browser. The slot editor includes Save, Compare, and Clear actions.
- **WoW-inspired character arrangement:** left/right armor and accessories columns, weapons at the bottom, and compact per-item stat summaries. A bottom panel sums the *mapped stat bonuses on your saved gear*; these are **not your complete character attributes**.
- **Equip from New Gear:** a persistent button and explicit replacement-slot selector appear alongside a candidate item. You decide whether to save it to your character regardless of the score. The previous recommendation-panel Equip button is also available whenever a character and candidate are selected.
- **Actual item icons where available:** ForeverDB catalog records with an icon name are displayed using the icon asset, not a generic star. The official ForeverDB embed provides fallback item tooltips and can add an icon when the record has an item ID. Missing icon metadata remains marked with a neutral placeholder rather than a fabricated icon.
- **Item search labels:** slot · required level · item subclass/type (e.g., Leather, Cloth, Two-Hand Sword), when ForeverDB publishes the necessary fields. An updated catalog run will populate these new metadata fields; older cached records may lack them.
- **Friend-facing cleanup:** no database administration or refresh interface is displayed on the site. Only repository maintainers can refresh the published catalog via GitHub Actions. The catalog is still read-only for visitors.
- **Small footer signature:** “Made by Morph.”

Preserved: all nine classes and specs, estimated/verified toggle, smarter unordered-word searches, gear ratings and plain-English recommendations, saved characters, local custom stat priorities, JSON backups, and documented source limitations.

## Publish V2.1 without starting an API refresh

1. In GitHub Desktop, **Fetch origin**, then **Pull origin** if offered.
2. Extract the ZIP and copy **only these four files** into the corresponding paths in your cloned repository, replacing the old versions:
   - `index.html`
   - `README.md`
   - `scripts/refresh_foreverdb.py`
   - `.github/workflows/refresh-foreverdb.yml`
3. **Do not delete or replace `data/foreverdb-items.json`**. Your existing downloaded catalog and its detailed item records remain intact.
4. In GitHub Desktop, commit as `Improve character equipment and icons (v2.1)` and **Push origin**.
5. The normal push publishes the current website and its existing catalog **without spending a ForeverDB API request**. Wait for a green Publish check on Actions, then Ctrl+Shift+R on the site.

## Private equipment catalog updates

`FOREVERDB_API_KEY` stays in GitHub Actions Secrets; never put it in the public HTML or share it in a message. The automation runs server-side on **schedule (daily check)** or via **Actions → Run workflow** by an authorized repository maintainer. ForeverDB does not document a webhook that notifies this site immediately when its data changes, so the daily check is the closest automatic approach at present.

The updated catalog script indexes **weapons and armor only** (ForeverDB classes 2 and 4, which also cover rings/trinkets/shields) and retrieves detailed records incrementally. It now also stores item subclass and icon names when ForeverDB provides them. It preserves valid prior stat details and progressively covers the remaining equipment records. The API is limited to 60 requests/minute and 10,000 requests/day per key, so completion can require multiple daily runs. Do not start overlapping updates. A successful run doesn't guarantee every item has a mapped numerical stat or every icon is available.

The workflow also automatically deploys the updated static catalog to the existing GitHub Pages website. Shared catalog refreshes never overwrite someone's saved character or personal stat priorities in their browser.

## Limitations and privacy

- **Estimated Mode** uses unverified class-specific stat priorities, not measured DPS or Blizzard-approved stat conversion formulas. **Verified Mode** refuses to produce a numerical performance score when required mechanics aren't known.
- Item procs, set bonuses, random suffixes, class restrictions, talent interactions and uncertain Forever item availability may not be fully modeled. Double-check real tooltips before equipping.
- Personal saved characters and custom priorities are held only in the browser on that device. Export them under **Advanced · Backup & transfer settings** before clearing browser data or switching devices. Neither ForeverDB nor GitHub receives your private character profiles from the comparator.
- Catalog metadata from ForeverDB may not include an icon or item subclass for every item. The site does not guess these values.

**API and tooltip reference pages checked:** November 3, 2026.
