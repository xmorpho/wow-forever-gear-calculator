# ⚔ WoW: Forever Gear Comparator — V2.3

**Made by Morph.** A free, unofficial gear companion for World of Warcraft: Forever. **Should I equip this new item?** Search for equipment, compare actual available tooltip attributes, and see an Equip / Keep / Too Close to Call recommendation based on your selected class and playstyle.

**Live website:** https://xmorpho.github.io/wow-forever-gear-calculator/

## Data credits

**Item data and embedded item tooltips are provided by [ForeverDB.net](https://foreverdb.net).** The application retains a visible source link alongside its item catalog and in its footer. Please retain that visible credit in future versions. ForeverDB's [developer rules](https://foreverdb.net/developers) require source attribution wherever its data is displayed. The official [tooltip integration](https://foreverdb.net/embed) is also included. WoW game assets belong to their respective owners. This website is not affiliated with Blizzard or ForeverDB.

## What's changed in V2.3

- **Missing icons:** The UI requests the official ForeverDB icon for items with an ID when the catalog lacks a usable icon filename. Item icon tiles fill their box; if the remote embed does not supply an image (network blocker, unsupported dynamic node), a neutral placeholder remains. The icon integration needs a live-site test.
- **Complete tooltip presentation:** Distinguishes **base armor** from primary bonuses and lists available **Equip/Use/Chance on hit** effects underneath the attributes in green. These are *displayed* and are **not automatically included in scoring**. The item's ForeverDB link opens the authoritative full tooltip.
- **Better catalog extraction:** The refresher stores armor and readable item-effect names/descriptions from individual ForeverDB records, plus available icon metadata. A known swim-speed spell effect (#8747) uses ForeverDB's published tooltip wording. Unknown effect names are preserved without fabricating a description.
- **Legacy cache enrichment:** Already downloaded records from V2.2 **do not include** the armor/effect descriptions discarded by the old parser. Running the workflow with **enrich_tooltips=true** requests those records again (within your daily API allowance) while retaining your previously mapped stats. This uses API requests but does not delete your progress. The scheduled refresh also enables enrichment.

## Existing V2.1 features

- **Click any empty or occupied character equipment slot** to open an item picker. Search within that slot, select an existing ForeverDB item, or enter a custom item name and the stats on your tooltip. Saved gear stays in your own browser. The slot editor includes Save, Compare, and Clear actions.
- **WoW-inspired character arrangement:** left/right armor and accessories columns, weapons at the bottom, and compact per-item stat summaries. A bottom panel sums the *mapped stat bonuses on your saved gear*; these are **not your complete character attributes**.
- **Equip from New Gear:** a persistent button and explicit replacement-slot selector appear alongside a candidate item. You decide whether to save it to your character regardless of the score. The previous recommendation-panel Equip button is also available whenever a character and candidate are selected.
- **Actual item icons where available:** ForeverDB catalog records with an icon name are displayed using the icon asset, not a generic star. The official ForeverDB embed provides fallback item tooltips and can add an icon when the record has an item ID. Missing icon metadata remains marked with a neutral placeholder rather than a fabricated icon.
- **Item search labels:** slot · required level · item subclass/type (e.g., Leather, Cloth, Two-Hand Sword), when ForeverDB publishes the necessary fields. An updated catalog run will populate these new metadata fields; older cached records may lack them.
- **Friend-facing cleanup:** no database administration or refresh interface is displayed on the site. Only repository maintainers can refresh the published catalog via GitHub Actions. The catalog is still read-only for visitors.
- **Small footer signature:** “Made by Morph.”

Preserved: all nine classes and specs, estimated/verified toggle, smarter unordered-word searches, gear ratings and plain-English recommendations, saved characters, local custom stat priorities, JSON backups, and documented source limitations.

## Publish V2.3 without starting an API refresh

1. In GitHub Desktop, **Fetch origin**, then **Pull origin** if offered.
2. Extract the ZIP and copy **only these four files** into the corresponding paths in your cloned repository, replacing the old versions:
   - `index.html`
   - `README.md`
   - `scripts/refresh_foreverdb.py`
   - `.github/workflows/refresh-foreverdb.yml`
3. **Do not delete or replace `data/foreverdb-items.json`**. Your existing downloaded catalog and its detailed item records remain intact.
4. In GitHub Desktop, commit as `V2.3 tooltip details and icon fixes` and **Push origin**.
5. The normal push publishes the current website and its existing catalog **without spending a ForeverDB API request**. Wait for a green Publish check on Actions, then Ctrl+Shift+R on the site.

## Private equipment catalog updates

`FOREVERDB_API_KEY` stays in GitHub Actions Secrets; never put it in the public HTML or share it in a message. The automation runs server-side on **schedule (daily check)** or via **Actions → Run workflow** by an authorized repository maintainer. ForeverDB does not document a webhook that notifies this site immediately when its data changes, so the daily check is the closest automatic approach at present.

The updated catalog script indexes **weapons and armor only** (ForeverDB classes 2 and 4, which also cover rings/trinkets/shields) and retrieves detailed records incrementally. It now also stores item subclass and icon names when ForeverDB provides them. It preserves valid prior stat details and progressively covers the remaining equipment records. The API is limited to 60 requests/minute and 10,000 requests/day per key, so completion can require multiple daily runs. Do not start overlapping updates. When the response includes a clearly named daily-remaining header, the updater stops before consuming the final 20 daily requests; otherwise it saves partial progress upon a 429.

### Restore missing armor/effect data on cached items

Do **not** start another large refresh until the API's daily allowance has reset and you have sufficient remaining requests. To enrich the records already downloaded, open **GitHub → Actions → Publish calculator and refresh ForeverDB catalog → Run workflow**:

- **detail_limit:** `8500` maximum, but use a lower number if unsure of your remaining daily quota.
- **force_details:** `false` (unchecked).
- **enrich_tooltips:** `true` (checked). This prioritizes existing cached records missing tooltip presentation fields, then moves on to unprocessed equipment. A large run can take hours at 60 requests/minute. Preserve the existing catalog JSON.

The first enrichment pass may show *the same number* of items with downloaded details, because it is adding **previously discarded armor and effect descriptions** to existing records rather than finding new items. Future runs can then resume adding new equipment. The scheduled workflow also enables this enrichment automatically.

ForeverDB limits API use to 60 requests/minute and 10,000/day per key. The updater tries to preserve 20 requests when remaining-quota headers are available, or stops on a 429 during details. Item index requests count too. Don't run simultaneous jobs. Changes become visible only after the entire workflow successfully publishes to GitHub Pages.

## Limitations and privacy

- **Estimated Mode** uses unverified class-specific stat priorities, not measured DPS or Blizzard-approved stat conversion formulas. **Verified Mode** refuses to produce a numerical performance score when required mechanics aren't known.
- Item procs, set bonuses, random suffixes, class restrictions, talent interactions and uncertain Forever item availability may not be fully modeled. Double-check real tooltips before equipping.
- Personal saved characters and custom priorities are held only in the browser on that device. Export them under **Advanced · Backup & transfer settings** before clearing browser data or switching devices. Neither ForeverDB nor GitHub receives your private character profiles from the comparator.
- Catalog metadata from ForeverDB may not include an icon or item subclass for every item. The site does not guess these values.

**API and tooltip reference pages checked:** November 3, 2026.

**Testing note:** The updater passed unit and mocked catalog-enrichment integration tests, and the inline JavaScript passed a syntax check. A live browser/icon integration test could not be completed here. The private API key and actual published catalog were not accessed. Please verify icon loading and item effect descriptions on the live site after publishing and enrichment.
