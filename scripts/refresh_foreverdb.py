#!/usr/bin/env python3
"""Refresh a static, attributed ForeverDB item catalog for GitHub Pages.

Requires FOREVERDB_API_KEY in GitHub Actions Secrets, never in public files.
API contract checked 2026-11-03: /api/v1/meta, /api/v1/items, /api/v1/items/{id};
responses use data + meta, limit <=100, X-API-Key auth, 60/min and 10000/day.
Details are cached and expanded incrementally to respect quotas.
Only class 2 (weapons) and class 4 (armor) are indexed/downloaded;
records explicitly marked as inventory slot 0 are excluded.
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
MAX_DETAILS = min(max(int(os.environ.get('MAX_DETAIL_REQUESTS', '8500')), 0), 8500)
FORCE = os.environ.get('FORCE_DETAILS', 'false').lower() == 'true'
ENRICH_TOOLTIPS = os.environ.get('ENRICH_TOOLTIPS', 'false').lower() == 'true'
DELAY = 1.15  # 52 req/min max, leaving headroom below ForeverDB's 60/minute limit
DAILY_REMAINING = None
DAILY_RESERVE = 20  # Avoid hitting the hard daily limit when headers reveal remaining quota
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
    global LAST_REQUEST, DAILY_REMAINING
    if DAILY_REMAINING is not None and DAILY_REMAINING <= DAILY_RESERVE:
        raise RateLimitError(f'Daily quota nearly exhausted ({DAILY_REMAINING} remaining); cache will be published')
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
                # ForeverDB documents X-Daily headers. Only interpret a clearly named
                # *remaining* count; header layouts can change between API versions.
                for header, value in resp.headers.items():
                    if 'daily' in header.lower() and 'remaining' in header.lower():
                        m = re.search(r'\d+', value)
                        if m:
                            DAILY_REMAINING = int(m.group())
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


def record(raw, detail=False, item_class_hint=None):
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

    fields = next((raw[k] for k in ('stats', 'attributes', 'statBonuses', 'bonusStats',
                                      'itemStats', 'statMods', 'itemMods', 'modifiers')
                   if isinstance(raw.get(k), (dict, list)) and len(raw[k]) > 0), {})
    if isinstance(fields, list):
        for entry in fields:
            if isinstance(entry, dict):
                label = (entry.get('name') or entry.get('statName') or entry.get('stat')
                         or entry.get('label') or entry.get('type') or entry.get('key')
                         or entry.get('statType') or entry.get('modifier'))
                if isinstance(label, dict):
                    label = label.get('name') or label.get('label') or label.get('key')
                value = entry.get('value', entry.get('amount', entry.get('points', entry.get('statValue', entry.get('val')))))
                if isinstance(label, str) and value is not None:
                    add(label, value)
    elif isinstance(fields, dict):
        for label, entry in fields.items():
            if isinstance(entry, (int, float, str)):
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
        item_class = item_class_hint
    if item_class is None:
        item_class = item_class_hint
    # Preserve item subclass for useful search labels, only when the API
    # provides a recognized client class/subclass classification.
    subclass_raw = next((raw[k] for k in (
        'subclass', 'subClass', 'subclassName', 'subClassName',
        'armorType', 'weaponType', 'itemSubclass', 'itemSubClass',
        'subclassId', 'itemSubclassName') if raw.get(k) is not None), None)
    if isinstance(subclass_raw, dict):
        sub_label = subclass_raw.get('name') or subclass_raw.get('label')
        subclass_raw = sub_label if sub_label else subclass_raw.get('id', subclass_raw.get('value'))
    armor_types = {1: 'Cloth', 2: 'Leather', 3: 'Mail', 4: 'Plate', 6: 'Shield'}
    weapon_types = {0: 'One-Hand Axe', 1: 'Two-Hand Axe', 2: 'Bow', 3: 'Gun',
                    4: 'One-Hand Mace', 5: 'Two-Hand Mace', 6: 'Polearm',
                    7: 'One-Hand Sword', 8: 'Two-Hand Sword', 10: 'Staff',
                    13: 'Fist Weapon', 15: 'Dagger', 16: 'Thrown',
                    18: 'Crossbow', 19: 'Wand', 20: 'Fishing Pole'}
    if isinstance(subclass_raw, (int, float)) or (isinstance(subclass_raw, str) and subclass_raw.strip().isdigit()):
        sub_id = int(subclass_raw)
        subclass = (armor_types if item_class == 4 else weapon_types if item_class == 2 else {}).get(sub_id, '')
    else:
        subclass = str(subclass_raw or '').strip()
    if subclass.lower() in ('none', 'unknown', 'other', 'miscellaneous'):
        subclass = ''
    if not subclass:
        # Do not infer material from item names. Accept only explicit API fields.
        for key in ('armorType', 'weaponType', 'subclassName', 'subClassName', 'itemSubclassName', 'equipmentType'):
            value = raw.get(key)
            if isinstance(value, dict):
                value = value.get('name') or value.get('label')
            if isinstance(value, str) and value.strip() and value.lower() not in ('other','unknown','none','miscellaneous'):
                subclass = value.strip()
                break
    icon_raw = next((raw.get(k) for k in (
        'icon', 'iconName', 'icon_name', 'iconFilename', 'iconFile',
        'iconPath', 'inventoryIcon', 'iconTexture', 'iconTextureName') if raw.get(k)), '')
    if isinstance(icon_raw, dict):
        icon_raw = (icon_raw.get('name') or icon_raw.get('filename')
                    or icon_raw.get('path') or icon_raw.get('iconName') or '')
    icon = str(icon_raw).strip()[:100]

    # Tooltip presentation is separate from scored numeric item bonuses.
    # Never guess unverified combat values from effect names.
    armor_data = raw.get('armor', raw.get('armorValue', raw.get('baseArmor', raw.get('armorRating'))))
    if isinstance(armor_data, dict):
        armor_data = armor_data.get('value', armor_data.get('amount', armor_data.get('armor')))
    armor = num(armor_data)
    if armor is None and item_class == 4:
        armor = stats.get('armor')
    if armor is not None and armor >= 0 and item_class == 4:
        stats['armor'] = armor  # Armor is also a numeric defensive bonus.
    effect_texts = []
    seen_effects = set()
    # WoW item spell trigger: 0=Use, 1=Equip, 2=Chance on hit.
    trigger_names = {0: 'Use', 1: 'Equip', 2: 'Chance on hit'}
    for field in ('effects', 'itemEffects', 'itemSpells', 'spells', 'equipEffects', 'useEffects', 'chanceOnHitEffects'):
        entries = raw.get(field)
        if isinstance(entries, dict):
            entries = list(entries.values())
        if not isinstance(entries, list):
            continue
        for effect in entries[:35]:
            if isinstance(effect, str):
                message, trigger = effect, 'Effect'
            elif isinstance(effect, dict):
                spell = effect.get('spell') if isinstance(effect.get('spell'), dict) else {}
                message = next((effect.get(k) for k in (
                    'tooltip', 'tooltipText', 'displayText', 'description', 'effectDescription',
                    'text', 'spellDescription', 'spellName', 'name') if isinstance(effect.get(k), str) and effect.get(k).strip()), None)
                message = message or next((spell.get(k) for k in ('description', 'tooltip', 'name') if isinstance(spell.get(k), str)), None)
                if not message:
                    continue
                # Verified public ForeverDB tooltip: spell 8747 means
                # 'Increases swim speed by 15%.' (e.g. Azure Silk Belt #7052).
                # Do not generalize this label to other spell IDs.
                if (str(effect.get('spellId', spell.get('id', ''))) == '8747' and
                        str(message).strip().lower().startswith('swimming speed')):
                    message = 'Increases swim speed by 15%.'
                code = effect.get('trigger', effect.get('triggerType', effect.get('spellTrigger')))
                try:
                    trigger = trigger_names.get(int(code), 'Effect')
                except (ValueError, TypeError):
                    trigger = ('Equip' if field == 'equipEffects' else 'Use' if field == 'useEffects' else
                               'Chance on hit' if field == 'chanceOnHitEffects' else 'Effect')
            else:
                continue
            message = re.sub(r'<[^>]*>', '', str(message)).strip()
            if not message:
                continue
            # Recognized full tooltip lines retain their original wording.
            if re.match(r'^(Equip|Use|Chance on hit|Passive)\s*:', message, re.I):
                line = message
            else:
                line = f'{trigger}: {message}'
            if line not in seen_effects:
                effect_texts.append(line[:260]);seen_effects.add(line)
    # The literal item-effect name in API responses may be less descriptive
    # than the rendered tooltip. The official embed supplies the full tooltip.
    binding = raw.get('binding', raw.get('bonding', ''))
    if isinstance(binding, dict):
        binding = binding.get('name') or binding.get('label') or ''
    return {
        'name': name[:100], 'remoteId': identifier, 'req': req,
        'quality': raw.get('quality') if isinstance(raw.get('quality'), int) else (raw.get('quality', {}).get('id') if isinstance(raw.get('quality'), dict) else None),
        'itemLevel': raw.get('itemLevel', raw.get('item_level', raw.get('level'))),
        'icon': icon, 'subclass': subclass[:45],
        'slot': slot[:50], 'stats': stats, 'source': 'ForeverDB',
        'display': ({'armor': armor if armor is not None and armor >= 0 else None,
                     'effects': effect_texts[:20], 'binding': str(binding or '')[:80]} if detail else {}),
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

    # ForeverDB supports server-side item class filters: 2=weapons, 4=armor.
    # This avoids spending catalog/detail quota on consumables, reagents and
    # crafting materials. Keep every equippable category across all classes.
    records = {}
    for item_class in (2, 4):
        offset = 0
        indexed_this_class = 0
        for page in range(500):
            obj = api_get(f'/items?class={item_class}&limit=100&offset={offset}')
            entries = array_from(obj)
            if not entries:
                break
            for raw in entries:
                parsed = record(raw, item_class_hint=item_class)
                if not parsed:
                    continue
                # Inventory type 0 explicitly means an item cannot be equipped.
                # An absent slot is not assumed to be 0; some list records omit it.
                raw_slot = raw.get('slot', raw.get('inventoryType', raw.get('inventorySlot', raw.get('equipSlot'))))
                if isinstance(raw_slot, dict):
                    raw_slot = raw_slot.get('id', raw_slot.get('value', raw_slot.get('name')))
                if str(raw_slot).strip().lower() in ('0', 'none', 'non-equippable', 'not equippable'):
                    continue
                parsed['_itemClass'] = item_class
                records[parsed['remoteId']] = parsed
                indexed_this_class += 1
            offset += len(entries)
            if page % 25 == 0:
                print(f'Indexed class {item_class}: {indexed_this_class:,} equippable candidates…', flush=True)
            m = obj.get('meta') or {}
            total = m.get('total') or ((m.get('pagination') or {}).get('total') if isinstance(m, dict) else None)
            try:
                total = int(total)
            except (ValueError, TypeError):
                total = None
            if (total is not None and offset >= total) or len(entries) < 100:
                break
        else:
            raise RuntimeError(f'Class {item_class} exceeded 50,000-item safety limit')
    print(f'Equipment-focused catalog: {len(records):,} weapons/armor records across all classes', flush=True)
    if len(records) < 100:
        raise RuntimeError(f'Only {len(records)} valid items received; refusing to replace catalog')

    # Retain detailed stats only when they belong to this game's build.
    for key, item in records.items():
        prev = existing.get(key)
        if prev and prev.get('hasDetail'):
            item['subclass'] = item.get('subclass') or prev.get('subclass', '')
            item['icon'] = item.get('icon') or prev.get('icon', '')
            item['stats'] = prev.get('stats', {})
            item['unmapped'] = prev.get('unmapped', [])
            item['display'] = prev.get('display') or {}
            item['hasDetail'] = True
            item['detailBuild'] = prev.get('detailBuild') or old_build or 'unknown'
            item['stale'] = build != 'unknown' and item['detailBuild'] != build
        else:
            item['stale'] = False

    # Spend individual detail calls only on weapons/armor; ignore beta-event copies.
    candidates = [it for it in records.values() if suitable_for_details(it) and not it.get('betaEvent')]
    candidates.sort(key=lambda x: (
        0 if ENRICH_TOOLTIPS and x.get('hasDetail') and not x.get('display') else
        1 if not x.get('hasDetail') or x.get('stale') else 2,
        x.get('speculation', False), x.get('req', 1) > 60, x.get('req', 1), x['remoteId']))
    print(f'Equipment detail candidates: {len(candidates):,}; already cached: {sum(bool(it.get("hasDetail")) and not it.get("stale", False) for it in candidates):,}; request budget {MAX_DETAILS:,}; API quota remaining {DAILY_REMAINING if DAILY_REMAINING is not None else "header unavailable"}', flush=True)
    updated = 0
    for item in candidates:
        if updated >= MAX_DETAILS:
            break
        if item.get('hasDetail') and not item.get('stale') and not FORCE:
            if not (ENRICH_TOOLTIPS and not item.get('display')):
                continue
        try:
            response = api_get(f"/items/{item['remoteId']}")
            parsed = record(single_from(response), detail=True, item_class_hint=item.get('_itemClass'))
            if parsed:
                # Preserve index name and item class if detailed response omits them.
                item['quality'] = parsed.get('quality') if parsed.get('quality') is not None else item.get('quality')
                item['itemLevel'] = parsed.get('itemLevel') or item.get('itemLevel')
                item['icon'] = parsed.get('icon') or item.get('icon')
                item['subclass'] = parsed.get('subclass') or item.get('subclass')
                # Keep already published presentation data when the newest response is sparse.
                old_display = item.get('display') or {}
                new_display = parsed.get('display') or {}
                item['display'] = {
                    'armor': new_display.get('armor') if new_display.get('armor') is not None else old_display.get('armor'),
                    'effects': new_display.get('effects') or old_display.get('effects') or [],
                    'binding': new_display.get('binding') or old_display.get('binding') or '',
                }
                # Do not silently erase known mapped bonuses when the API supplies
                # sparse details, or when a new response shape is not yet understood.
                previous_stats = item.get('stats') or {}
                old_detail_build = item.get('detailBuild')
                if parsed['stats'] or not previous_stats:
                    # On the same build, merge fields: incomplete API shapes
                    # must not erase stats already obtained for this build.
                    item['stats'] = ({**previous_stats, **parsed['stats']} if
                                     old_detail_build == build else parsed['stats'])
                    item['unmapped'] = parsed['unmapped']
                    item['detailBuild'] = build
                    item['stale'] = False
                else:
                    item['stale'] = True
                    item['unmapped'] = list(dict.fromkeys((item.get('unmapped') or []) +
                                            ['New detail response did not map to known stats']))[:12]
                    print(f'WARN item {item["remoteId"]}: new detail has no mapped bonuses; retained prior cached values as stale', flush=True)
                item['hasDetail'] = True
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
            'mappedDetailRecords': sum(bool(it.get('stats')) for it in items),
            'tooltipEnhancedRecords': sum(bool(it.get('display')) for it in items),
            'dailyQuotaRemainingAtEnd': DAILY_REMAINING,
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
