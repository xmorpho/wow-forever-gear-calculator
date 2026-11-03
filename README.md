# WoW: Forever Gear Comparison Calculator

A free, unofficial, fan-made gear comparison calculator for the **nine World of Warcraft: Forever classes**, hosted using GitHub Pages.

**Live calculator:** https://xmorpho.github.io/wow-forever-gear-calculator/

## ForeverDB credit and terms

**Item data provided by [ForeverDB.net](https://foreverdb.net).** ForeverDB is the source of the item database. Attribution is also displayed in the calculator's interface beside the item search, catalog controls, and page footer. This independent project is not affiliated with ForeverDB or Blizzard Entertainment.

The database is a snapshot, and items or availability may change. Tooltip values take priority. **Some items are indexed before detailed stats have been fetched**. Unmapped bonuses, procs, and use/equip effects are not scored. Beta-event-only and speculative availability flags are not confirmations of obtainability.

## Publish the site

Copy these files and folders to the **root** of the `main` branch of this repository, keeping the structure:

```text
index.html
README.md
data/foreverdb-items.json
scripts/refresh_foreverdb.py
.github/workflows/refresh-foreverdb.yml
```

**Important:** Under **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions** (not "Deploy from a branch"). The included workflow deploys the site when code changes and immediately after catalog refreshes, because commits created with `GITHUB_TOKEN` don't trigger branch-based Pages builds.

## Private API key

The repository owner creates the secret **`FOREVERDB_API_KEY`** in **Settings → Secrets and variables → Actions**. Never paste the key into `index.html`, a GitHub issue, a commit, or a public chat.

## Get and refresh the catalog

1. In the repository, open **Actions → Refresh ForeverDB catalog**.
2. Click **Run workflow**, select the `main` branch, and click the green **Run workflow** button.
3. The action downloads the full paginated item-name index and **up to 1,500 item details** in one run by default, keeping all previously retrieved detail records. Item details progressively become available as the action is run again.
4. Once the workflow shows a green check, the action commits `data/foreverdb-items.json` to `main` and **directly deploys** the refreshed catalog to GitHub Pages. The calculator will load it when users next visit or click **Reload published catalog** in Catalog status & refresh.
5. A daily scheduled refresh is configured. Manually run extra batches using `detail_limit` where needed, while respecting ForeverDB's documented limits.

The public site does **not** call ForeverDB with your secret. Only the repository's GitHub Actions workflow sends authenticated requests.

ForeverDB documents **60 requests/minute** and **10,000 requests/day** per key. The updater throttles requests and caps detail calls to leave headroom for paging and other API users. Repeated manual runs share the daily allowance; avoid parallel/manual runs close together.

## Calculator usage and limitations

- Choose class, specialization, level, and playstyle.
- Search the shared catalog in either item panel. Selecting an item applies its published numeric stats when available, or leaves stats for manual entry when absent.
- Both comparison items remain editable.
- **Estimated mode:** numerical relative weights are *illustrative and adjustable*, not verified WoW DPS/healing calculations.
- **Verified mode:** no numerical score is shown if mechanics required for the comparison aren't documented.
- Export/import individual configurations and optional personal item lists; these stay separate from the public catalog.

No commercial affiliation or endorsement is implied.
