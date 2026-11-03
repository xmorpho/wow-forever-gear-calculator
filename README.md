# ⚔ WoW: Forever Gear Comparator — Version 2.0

A free, unofficial World of Warcraft: Forever equipment comparison website for all nine classes. **Should you equip that new piece of gear?** Search for two items, compare their available tooltip attributes and see a player-friendly Equip / Keep / Too Close to Call recommendation with the reasons behind it.

**Website:** https://xmorpho.github.io/wow-forever-gear-calculator/

## Data attribution and usage

**Item data and live tooltip embedding are provided by [ForeverDB.net](https://foreverdb.net)**. Please preserve this visible attribution in the item catalog controls, item links and website footer. ForeverDB requires a visible credit link wherever its data appears. See [ForeverDB's developer rules](https://foreverdb.net/developers) and [embeddable tooltip guide](https://foreverdb.net/embed).

This fan-made tool is not affiliated with Blizzard Entertainment or ForeverDB. ForeverDB's client-derived records can include uncertain or historical beta items; a database entry is not proof an item is obtainable. Do not resell the data.

## Version 2 features

- Nine classes, specialization selection, levels 1–60 and five playstyles.
- **Estimated Mode:** Editable, unverified stat-priority estimates. A displayed upgrade percentage is *not* an actual DPS, survivability or mana-per-second prediction.
- **Verified Mode:** Only documented attribute relationships and tooltip differences; no fabricated gear rating or winner when critical combat formulas are unknown.
- **Smarter searching:** Search any words in any order, case-insensitive, with relevance-first matches, optional typo fallback, optional category/slot/level/rarity filters and expandable results.
- **Compact equipment cards:** Item names, available tooltip stats, level restrictions and ForeverDB item links/embedded tooltip support. The official ForeverDB script can load icons, item rarity styling and additional tooltip lines from their service. An icon fallback is displayed if the external embed cannot load.
- **Responsive workspace:** Current Gear / New Gear / Recommendation in three columns on wide displays; rearranged on smaller screens.
- **My Character:** Save up to 20 character profiles and their equipment slots in each person's browser. Clicking an equipped slot loads it into Current Gear; searching for a new drop automatically pulls the matching equipped slot when possible. Equipment changes require explicit confirmation. The planner does **not** change the WoW client.
- **Personal stat priorities:** Changes are saved locally per class/spec/playstyle. Other users aren't affected. The recommended defaults can be restored independently.
- Backup/export/import of saved characters and priorities through **Advanced · Backup & transfer settings**.
- ForeverDB attribution beside the catalog and in the persistent footer.

## Publish Version 2 to the existing GitHub Pages site

**Fast preview first:** A normal code push will *only publish V2* using the existing `data/foreverdb-items.json`. It deliberately skips ForeverDB requests, so you can test the redesigned site with your current ~1,500 detailed records before starting any lengthy equipment-only refresh. Do **not** click Run workflow until you are ready for step two. The equipment-only index takes effect only when that later refresh runs.

**Do not replace or delete `data/foreverdb-items.json`.** That file already contains the real item catalog you've downloaded through GitHub Actions. This update deliberately omits it so your detailed records are preserved.

1. In GitHub Desktop, **Fetch/Pull origin** to bring your existing `main` branch up to date. You should see `data/foreverdb-items.json` in your local repository.
2. Extract the upgrade ZIP and copy its **four files** into the root of your cloned repository, keeping folders: `index.html`, `README.md`, `scripts/refresh_foreverdb.py`, `.github/workflows/refresh-foreverdb.yml`.
3. Replace the matching files but **keep your existing `data/` folder and its JSON file**.
4. Commit with a name like **"Release gear comparator v2"** and click **Push origin**.
5. Wait for the green check on the **Publish calculator and refresh ForeverDB catalog** Actions run. Refresh the site using **Ctrl + Shift + R**.
6. Your website URL remains exactly the same: https://xmorpho.github.io/wow-forever-gear-calculator/

GitHub Pages should remain set to **Settings → Pages → Source: GitHub Actions**. The workflow publishes the existing catalog when you push code changes; it does not spend API quota on every code push.

## Automatic ForeverDB catalog expansion

The private GitHub workflow reads `FOREVERDB_API_KEY` only from **repository Actions Secrets**, not from the HTML or public JSON. Never paste a key into code or issues.

The workflow downloads the complete **equipment-focused** name index (ForeverDB item classes 2 and 4: weapons and armor, including rings, trinkets, accessories and off-hands) and stores detailed gear item records incrementally in `data/foreverdb-items.json`. Items explicitly marked with inventory slot 0 are excluded. Consumables, crafting materials, and unrelated item classes are not indexed. Class/slot classification is based on ForeverDB metadata and can be incomplete for unusual items.

**Version 2 increases the default maximum to 8,500 detailed requests per scheduled/manual run** (from 1,500), leaving headroom beneath ForeverDB's documented **60 requests/minute and 10,000/day** per key. Runs are throttled and cached; subsequent days progressively expand coverage while preserving previously downloaded details. Initial catch-up can require multiple days. Existing daily scheduled updates continue, and manual runs are available through **Actions → Publish calculator and refresh ForeverDB catalog → Run workflow**. Avoid concurrent runs, and remember multiple runs share the same daily quota.

**Important:** The full search index does not mean every item already has detailed numeric stats. Item pages and the official embedded tooltip can show additional data, but unsupported effects and records that have not yet been fetched are *not* silently scored. The website will tell users when there aren't enough mapped numbers to make a recommendation. If the site's data hasn't refreshed yet, use the repository workflow to advance the cache.

## Accuracy notes

Estimated points and category weights are explicitly **assumptions**, not confirmed Forever mechanics. The algorithm does not silently borrow TBC/Retail conversion tables. Hunter pet and Druid Feral mechanics reflect available Forever references, with uncertain total impact clearly qualified. Missing enchants, special procs, set bonuses, random suffixes, class restrictions and weapon-hand interactions can change which gear is truly preferable. Check real in-game tooltips.

Source material is linked in the calculator's **Verification sources** section. API/embed reference pages were checked 2026-11-03.

## Local character data

Saved characters, equipment and weight overrides are stored on the player's current browser/device, not on the GitHub website or in ForeverDB. Browser data clearing can remove them. Use **Advanced → Backup & transfer settings → Export saved characters + priorities** for backups or to move to another device. Public default weight changes don't silently overwrite someone's private custom settings.

## Equipment-focused optimization (November 3, 2026)

This edition of the Version 2 ZIP narrows **both search-index requests and detailed-item requests** to ForeverDB class IDs 2 (weapons) and 4 (armor); excludes records explicitly marked inventory slot 0; preserves any previously fetched details for retained items; and publishes the refreshed searchable catalog to the same GitHub Pages website. Different classes can still search all their gear.

The *index item count* will likely become smaller than the previous 22,499 names, by design. The detailed-record count may also shrink as non-equipment records are omitted; this does not mean cached equipment records were lost.

**To get more details tonight:** First push the four files. Pushing code deploys V2 but does not call ForeverDB. Then from GitHub **Actions → Publish calculator and refresh ForeverDB catalog → Run workflow**, choose `detail_limit` **7000** (a conservative target if today's earlier ~1,500-detail run used the same key; other requests also consume the shared daily quota). The process is throttled to about 52 requests/minute; thousands of details take hours. Do not launch overlapping refreshes. The API's daily counter resets at UTC midnight, not according to your local time. When the run completes, check the log's final line and compare `detailRecords` with the new equipment index size; a successful run does not necessarily mean every item has usable mapped stats. If needed, run a second refresh after the daily quota resets.

**Note:** ForeverDB's list endpoint is documented with `class=2` and `class=4` filters. The static updater uses no client-side API key and never puts the secret in published files.
