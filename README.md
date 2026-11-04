# WoW: Forever Gear Comparator — Version 2.5 review candidate

**Do not publish this review candidate until approved.** This package is separate from the interactive sample preview.

## Changes

- Removes the prominent percentage increase from Estimated Mode because item-only scores can create enormous, misleading values from a weak baseline.
- Places Damage potential, Survivability, Resource efficiency and Healing/utility **side-by-side category bars** in the main recommendation. Each category uses its own pairwise scale (current vs candidate); this does not measure DPS, healing output, or actual combat performance.
- Leaves exact ratings and calculated category points under Detailed Analysis, and preserves Verified Mode's no-numerical-score restriction.
- Explains specific item stat deltas, including Frost Damage for a Frost Mage.
- Improves updater recognition of explicit static school-damage tooltip labels (e.g. `Frost Damage Done`) and equipment effects that use an explicit Equip trigger.
- Prevents a misleading direct Equip/Keep recommendation for two different equipment slots.

## Known limitations

- Existing cached detail records that omitted bonuses cannot magically gain them from this code update. To populate missing Frost Damage, the owner must refresh/enrich item details when the ForeverDB quota allows, or enter the stat from the in-game tooltip. No user API key is in these files.
- The separate icon-sizing fix from 2.4.1 is included in this review candidate. It still needs real-provider validation on the user's computer; the preview screenshot has intentionally blocked external icon downloads. This package does **not** claim that remote icons are fixed.
- Neither the comparison bars nor rating values are actual performance % changes. All numerical default stat priorities remain estimates.

## When approved for publishing

Replace only `index.html` and `scripts/refresh_foreverdb.py`, preserving all other files, especially `data/foreverdb-items.json` and `.github/workflows/refresh-foreverdb.yml`. Push to main as usual. A standard push deploys the website without running a full catalog refresh.

Item data and item links: [ForeverDB.net](https://foreverdb.net). An independent fan project by Morph.
