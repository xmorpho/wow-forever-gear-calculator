#!/usr/bin/env python3
"""Refresh a static, attributed ForeverDB item catalog for GitHub Pages.

Requires FOREVERDB_API_KEY in GitHub Actions Secrets, never in public files.
API contract checked 2026-11-03: /api/v1/meta, /api/v1/items, /api/v1/items/{id};
responses use data + meta, limit <=100, X-API-Key auth, 60/min and 10000/day.
Details are cached and expanded incrementally to respect quotas.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://foreverdb.net/api/v1'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'foreverdb-items.json'
KEY = os.environ.get('FOREVERDB_API_KEY', '').strip()
MAX_DETAILS = min(max(int(os.environ.get('MAX_DETAIL_REQUESTS', '1500')), 0), 8500)
FORCE = os.environ.get('FORCE_DETAILS', 'false').lower() == 'true'
DELAY = 1.15  # 52 req/min max, leaving headroom below ForeverDB's 60/minute limit
LAST_REQUEST = 0.0

SUPPORTED = {
    'str', 'agi', 'sta', 'int', 'spi', 'sp', 'heal', 'ap', 'rap', 'mp5',
    'armor', 'hp', 'mana', 'spellpen', 'expertise', 'skill', 'def', 'blockval',
    'resist', 'fire', 'frost', 'arcane', 'nature', 'shadow', 'holy', 'petd',
    'crit', 'hit', 'haste', 'crating', 'hrating', 'hasterating', 'dodge',
    'parry', 'block', 'wdps', 'speed', 'avoid',
}
ALIASES = {
    'strength': 'str', 'agility': 'agi', 'stamina': 'sta', 'intellect': 'int',
    'spirit': 'spi', 'spell power': 'sp', 'spell damage': 'sp',
    'damage and healing': 'sp', 'healing power': 'heal',
    'healing done': 'heal', 'healing spells': 'heal', 'bonus healing': 'heal',
    'attack power': 'ap', 'melee attack power': 'ap', 'ranged attack power': 'rap',
    'mana per 5': 'mp5', 'mana every 5': 'mp5', 'mana regeneration per 5': 'mp5',
    'armor': 'armor', 'health': 'hp', 'mana': 'mana',
    'spell penetration': 'spellpen', 'expertise': 'expertise',
    'weapon skill': 'skill', 'defense': 'def', 'block value': 'blockval',
    'all resistances': 'resist', 'fire damage': 'fire',
    'frost damage': 'frost', 'arcane damage': 'arcane',
    'nature damage': 'nature', 'shadow damage': 'shadow',
    'holy damage': 'holy', 'pet damage': 'petd',
}

class RateLimitError(Exception):
    pass


def api_get(path):
    global LAST_REQUEST
    if not KEY:
        raise RuntimeError('Missing FOREVERDB_API_KEY GitHub Actions secret')
    elapsed = time.monotonic() - LAST_REQUEST
    if LAST_REQUEST and elapsed < DELAY:
        time.sleep(DELAY - elapsed)
    req = urllib.request.Request(BASE + path, headers={
        'X-API-Key': KEY, 'Accept': 'application/json',
        'User-Agent': 'WowForeverGearCalculator/1.0 (https://github.com/xmorpho/wow-forever-gear-calculator)',
    })
    for attempt in range(3):
        LAST_REQUEST = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                obj = json.load(resp)
                if not isinstance(obj, dict):
                    raise ValueError('Unexpected ForeverDB response format')
                return obj
        except urllib.error.HTTPError as err:
            if err.code == 429:
                # Do not wait hours when daily quota is exhausted.
                raise RateLimitError('ForeverDB rate limit reached (HTTP 429); resume at next refresh') from err
            if err.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f'ForeverDB returned HTTP {err.code} for {path}') from err
        except (TimeoutError, urllib.error.URLError) as err:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f'ForeverDB request failed for {path}: {err}') from err
    raise RuntimeError('Unable to complete ForeverDB request')


def array_from(obj):
    data = obj.get('data', obj)
    if isinstance(data, list):
        return data
    for candidate in (data, obj):
        if isinstance(candidate, dict):
            for key in ('items', 'results'):
                if isinstance(candidate.get(key), list):
                    return candidate[key]
    raise ValueError('Unrecognized item-list response; inspect the current ForeverDB API schema')


def single_from(obj):
    data = obj.get('data', obj)
    if isinstance(data, dict):
        return data.get('item', data)
    raise ValueError('Unrecognized item-detail response')


def stat_key(name):
    if not isinstance(name, str):
        return None
    orig = name.lower()
    n = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    n = re.sub(r'[_-]', ' ', n).lower()
    n = re.sub(r'\b(item mod|bonus|increases|rating|short)\b', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    if 'critical' in n or 'crit' in n:
        return 'crating' if 'rating' in orig else ('crit' if ('chance' in orig or '%' in orig or 'percent' in orig) else 'crating')
    if 'hit' in n:
        return 'hrating' if 'rating' in orig else ('hit' if ('chance' in orig or '%' in orig or 'percent' in orig) else 'hrating')
    if 'haste' in n:
        return 'hasterating' if 'rating' in orig else ('haste' if ('chance' in orig or '%' in orig or 'percent' in orig) else 'hasterating')
    if 'dodge' in n:
        return 'dodge' if ('chance' in orig or '%' in orig or 'percent' in orig) else None
    if 'parry' in n:
        return 'parry' if ('chance' in orig or '%' in orig or 'percent' in orig) else None
    if 'block' in n and n != 'block value':
        return 'block' if ('chance' in orig or '%' in orig or 'percent' in orig) else None
    return ALIASES.get(n) or (n if n in SUPPORTED else None)


def num(value):
    try:
        f = float(value)
        if f != f or abs(f) > 1000000:
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None


def record(raw, detail=False):
    if not isinstance(raw, dict):
        return None
    identifier = raw.get('id', raw.get('itemId', raw.get('itemID')))
    try:
        identifier = int(identifier)
        if identifier <= 0:
            return None
    except (ValueError, TypeError):
        return None
    name = str(raw.get('name') or raw.get('itemName') or raw.get('displayName') or '').strip()
    if not name:
        return None
    req = raw.get('requiredLevel', raw.get('required_level', raw.get('requireLevel', raw.get('minLevel', raw.get('levelRequired', raw.get('level', 1))))))
    try:
        req = max(1, min(int(req), 100))
    except (TypeError, ValueError):
        req = 1
    slot_raw = raw.get('slot', raw.get('inventoryType', raw.get('inventorySlot', raw.get('equipSlot', 'Other'))))
    if isinstance(slot_raw, dict):
        slot = str(slot_raw.get('name') or slot_raw.get('label') or slot_raw.get('id') or 'Other')
    else:
        slot = str(slot_raw)
    stats, unmapped = {}, []

    def add(label, value):
        key = stat_key(label)
        value = num(value)
        if key and value is not None:
            stats[key] = value
        elif label and len(unmapped) < 12:
            unmapped.append(str(label)[:80])

    fields = raw.get('stats') or raw.get('attributes') or raw.get('statBonuses') or {}
    if isinstance(fields, list):
        for entry in fields:
            if isinstance(entry, dict):
                label = entry.get('name') or entry.get('statName') or entry.get('stat') or entry.get('label') or entry.get('type') or entry.get('key')
                value = entry.get('value', entry.get('amount', entry.get('points', entry.get('statValue', entry.get('val')))))
                if isinstance(label, str) and value is not None:
                    add(label, value)
    elif isinstance(fields, dict):
        for label, entry in fields.items():
            if isinstance(entry, (int, float)):
                add(label, entry)
            elif isinstance(entry, dict):
                label = entry.get('name') or entry.get('statName') or label
                value = entry.get('value', entry.get('amount', entry.get('points', entry.get('statValue'))))
                if value is not None:
                    add(label, value)

    damage = raw.get('weapon') or raw.get('weaponDamage') or raw.get('damage') or {}
    if not isinstance(damage, dict):
        damage = {}
    speed = num(raw.get('weaponSpeed', raw.get('speed', damage.get('speed'))))
    if speed and speed > 0:
        if speed > 100:
            speed = speed / 1000
        stats['speed'] = round(speed, 4)
    dps = num(raw.get('weaponDps', raw.get('weaponDPS', raw.get('dps', damage.get('dps', damage.get('damagePerSecond'))))))
    if dps is None and speed and speed > 0:
        low = num(damage.get('min', damage.get('minDamage')))
        high = num(damage.get('max', damage.get('maxDamage')))
        if low is not None and high is not None:
            dps = (low + high) / 2 / speed
    if dps is not None and dps >= 0:
        stats['wdps'] = round(dps, 4)

    class_raw = raw.get('itemClass', raw.get('class', raw.get('classId')))
    if isinstance(class_raw, dict):
        class_raw = class_raw.get('id', class_raw.get('value'))
    try:
        item_class = int(class_raw)
    except (TypeError, ValueError):
        item_class = None
    return {
        'name': name[:100], 'remoteId': identifier, 'req': req,
        'slot': slot[:50], 'stats': stats, 'source': 'ForeverDB',
        'hasDetail': bool(detail), 'unmapped': unmapped,
        'betaEvent': bool(raw.get('betaEvent', False)),
        'speculation': bool(raw.get('speculation', False)),
        'speculationReasons': [str(v)[:100] for v in raw.get('speculationReasons', [])[:5]] if isinstance(raw.get('speculationReasons'), list) else [],
        '_itemClass': item_class,
    }


def suitable_for_details(item):
    kind = item.get('_itemClass')
    if kind is not None:
        return kind in (2, 4)
    # For unknown class IDs, prioritize visibly equippable slots, not consumables.
    slot = str(item.get('slot', '')).lower()
    return slot not in ('other', '0', 'none', 'unknown', 'null', '')


def extract_build(obj):
    meta = obj.get('meta') if isinstance(obj, dict) else {}
    data = obj.get('data') if isinstance(obj, dict) else {}
    for source in (data, meta, obj):
        if isinstance(source, dict):
            for key in ('gameBuild', 'clientBuild', 'build', 'dataBuild'):
                v = source.get(key)
                if isinstance(v, (str, int)):
                    return str(v)
    return None


def refresh():
    print('Requesting ForeverDB metadata…', flush=True)
    meta_response = api_get('/meta')
    build = extract_build(meta_response) or 'unknown'
    existing = {}
    old_build = None
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            old_build = previous.get('meta', {}).get('build')
            existing = {int(it['remoteId']): it for it in previous.get('items', []) if it.get('remoteId')}
        except (ValueError, TypeError, KeyError) as err:
            print('Existing cache unreadable, building clean index:', err, flush=True)
    print(f'Catalog build: {build}; previous: {old_build or "none"}', flush=True)

    records = {}
    offset = 0
    for page in range(500):
        obj = api_get(f'/items?limit=100&offset={offset}')
        entries = array_from(obj)
        if not entries:
            break
        for raw in entries:
            parsed = record(raw)
            if parsed:
                records[parsed['remoteId']] = parsed
        offset += len(entries)
        if page % 25 == 0:
            print(f'Indexed {len(records):,} items…', flush=True)
        m = obj.get('meta') or {}
        total = m.get('total') or ((m.get('pagination') or {}).get('total') if isinstance(m, dict) else None)
        try:
            total = int(total)
        except (ValueError, TypeError):
            total = None
        if (total is not None and offset >= total) or len(entries) < 100:
            break
    else:
        raise RuntimeError('Catalog exceeded the 50,000-item safety limit')
    if len(records) < 100:
        raise RuntimeError(f'Only {len(records)} valid items received; refusing to replace catalog')

    # Retain detailed stats only when they belong to this game's build.
    for key, item in records.items():
        prev = existing.get(key)
        if prev and prev.get('hasDetail'):
            item['stats'] = prev.get('stats', {})
            item['unmapped'] = prev.get('unmapped', [])
            item['hasDetail'] = True
            item['detailBuild'] = prev.get('detailBuild') or old_build or 'unknown'
            item['stale'] = build != 'unknown' and item['detailBuild'] != build
        else:
            item['stale'] = False

    # Prioritize all equippable gear. Unknown item types remain searchable by name.
    candidates = [it for it in records.values() if suitable_for_details(it) and not it.get('betaEvent')]
    candidates.sort(key=lambda x: (not x.get('stale', False) and x.get('hasDetail', False), x.get('speculation', False), x.get('req', 1) > 60, x.get('req', 1), x['remoteId']))
    updated = 0
    for item in candidates:
        if updated >= MAX_DETAILS:
            break
        if item.get('hasDetail') and not item.get('stale') and not FORCE:
            continue
        try:
            response = api_get(f"/items/{item['remoteId']}")
            parsed = record(single_from(response), detail=True)
            if parsed:
                # Preserve index name and item class if detailed response omits them.
                item['stats'] = parsed['stats']
                item['unmapped'] = parsed['unmapped']
                item['hasDetail'] = True
                item['detailBuild'] = build
                item['stale'] = False
        except RateLimitError as err:
            print('Quota reached; publishing available cached records:', err, flush=True)
            break
        except (RuntimeError, ValueError) as err:
            print('Skipping detail after error:', item['remoteId'], err, flush=True)
        updated += 1
        if updated % 100 == 0:
            print(f'Processed {updated:,} item details…', flush=True)

    items = []
    for item in sorted(records.values(), key=lambda x: x['remoteId']):
        item.pop('_itemClass', None)
        # Stable user-facing ID generated by the client from remoteId.
        items.append(item)
    result = {
        'meta': {
            'source': 'ForeverDB', 'sourceUrl': 'https://foreverdb.net',
            'build': build, 'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
            'indexedItems': len(items),
            'detailRecords': sum(bool(it.get('hasDetail')) for it in items),
            'staleRecords': sum(bool(it.get('stale')) for it in items),
            'detailRequestsThisRun': updated,
        },
        'items': items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print('Saved', OUT, f"{len(items):,} names, {result['meta']['detailRecords']:,} detailed records, {result['meta']['staleRecords']:,} stale details", flush=True)


if __name__ == '__main__':
    try:
        refresh()
    except Exception as exc:
        print('Catalog refresh failed:', exc, file=sys.stderr, flush=True)
        raise SystemExit(1)
