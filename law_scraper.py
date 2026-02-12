#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Law tracker scraper (notification-less).
- Fetch e-Gov public comment RSS
- Filter safety-related items
- Update public/data/items.json with safe merge (preserve manual edits)
- Cache raw hash in public/data/cache/last-fetch.json
"""
import json
import hashlib
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import feedparser

RSS_URL = "https://public-comment.e-gov.go.jp/rss/pcm_list_0000000046.xml"

SAFETY_REGEX = re.compile(
    r"(労働安全衛生|安全衛生|労災|化学物質|石綿|高年齢|作業環境|特定化学物質|有機溶剤|粉じん|鉛|酸素欠乏|"
    r"電離放射線|ボイラー|クレーン|熱中症|墜落|感電|保護具|リスクアセスメント)"
)

ITEMS_PATH = os.path.join("public", "data", "items.json")
CACHE_PATH = os.path.join("public", "data", "cache", "last-fetch.json")

TEMPLATE_SUMMARY = [
    "自動取得された案件です",
    "詳細は一次ソースを確認してください",
    "手動でsummary_3を更新してください",
]


def iso_day_jst() -> str:
    # JST = UTC+9
    now = datetime.now(timezone.utc).astimezone(timezone.utc)
    # keep simple: use UTC date; UI can interpret. If you prefer JST, adjust here.
    return now.date().isoformat()


def md5_text(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def normalize_url(url: str) -> str:
    u = (url or "").strip().lower()
    # keep query to avoid collisions; remove trailing slash only
    u = re.sub(r"/$", "", u)
    return u


def fixed_id_from_url(url: str) -> str:
    return md5_text(normalize_url(url))


def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def hash_raw(raw: Any) -> str:
    return md5_text(json.dumps(raw, ensure_ascii=False, sort_keys=True))


def is_template_summary(summary_3: List[str]) -> bool:
    return (
        isinstance(summary_3, list)
        and len(summary_3) == 3
        and summary_3[0] == TEMPLATE_SUMMARY[0]
        and summary_3[1] == TEMPLATE_SUMMARY[1]
        and summary_3[2] == TEMPLATE_SUMMARY[2]
    )


def union_tags(a: List[str], b: List[str]) -> List[str]:
    return list(dict.fromkeys((a or []) + (b or [])))


def union_sources(existing: List[Dict[str, str]], incoming: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # existing-first (preserve manual label changes)
    m: Dict[str, Dict[str, str]] = {}
    for s in (existing or []):
        url = (s or {}).get("url", "")
        if url:
            m[url] = s
    for s in (incoming or []):
        url = (s or {}).get("url", "")
        if url and url not in m:
            m[url] = s
    return list(m.values())


def safe_merge(existing: Dict[str, Any], auto: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing)

    existing_tags = existing.get("tags") or []
    auto_tags = auto.get("tags") or []

    # 1) always overwrite
    for k in ["title", "process", "action", "updated_at"]:
        merged[k] = auto.get(k)

    # 2) dates key-merge
    merged["dates"] = dict(existing.get("dates") or {})
    for k, v in (auto.get("dates") or {}).items():
        if v:
            merged["dates"][k] = v

    # 3) sources union
    merged["sources"] = union_sources(existing.get("sources") or [], auto.get("sources") or [])

    # 4) manual fields: overwrite only if needs_review OR empty
    has_needs_review = "needs_review" in existing_tags

    def should_overwrite(field: str) -> bool:
        val = existing.get(field)
        if has_needs_review:
            return True
        if field in ["summary_3", "target", "actions"]:
            return not val or (isinstance(val, list) and len(val) == 0)
        return not val

    for field in ["summary_3", "target", "risk_if_delayed", "actions"]:
        if should_overwrite(field):
            merged[field] = auto.get(field)

    # 5) tags union + auto remove needs_review if summary changed
    tags = union_tags(existing_tags, auto_tags)
    summary = merged.get("summary_3") or []
    if (not is_template_summary(summary)) and ("needs_review" in tags):
        tags = [t for t in tags if t != "needs_review"]
        if "reviewed" not in tags:
            tags.append("reviewed")
    merged["tags"] = tags

    return merged


def map_to_item(entry: Dict[str, Any]) -> Dict[str, Any]:
    url = entry.get("link") or ""
    title = entry.get("title") or "タイトル未取得"
    content = entry.get("summary") or entry.get("description") or ""

    item_id = fixed_id_from_url(url)
    today = iso_day_jst()

    auto = {
        "id": item_id,
        "title": title,
        "law_family": "労働安全衛生関連法令",
        "topic": "要確認",
        "process": "public_comment",
        "action": "PREPARE",
        "summary_3": TEMPLATE_SUMMARY[:],
        "target": ["要確認"],
        "dates": {},  # MVP: empty ok
        "risk_if_delayed": "要確認",
        "actions": [
            {"text": "一次ソースを確認", "owner": "安全"},
            {"text": "対応要否を判断", "owner": "安全"},
        ],
        "sources": [{"label": "egov-pubcom", "url": url}],
        "tags": ["needs_review", "auto_generated"],
        "updated_at": today,
    }

    # optional: put opened/deadline into tags if present in content (very loose)
    m_open = re.search(r"公示日[：:]\s*(\d{4})/(\d{1,2})/(\d{1,2})", content)
    if m_open:
        y, mo, d = m_open.group(1), m_open.group(2).zfill(2), m_open.group(3).zfill(2)
        auto["tags"].append(f"公示:{y}-{mo}-{d}")

    m_dead = re.search(r"(締切|受付締切)[^0-9]*(\d{4})/(\d{1,2})/(\d{1,2})", content)
    if m_dead:
        y, mo, d = m_dead.group(2), m_dead.group(3).zfill(2), m_dead.group(4).zfill(2)
        auto["tags"].append(f"締切:{y}-{mo}-{d}")

    return auto


def main():
    feed = feedparser.parse(RSS_URL)

    raw_items: List[Dict[str, Any]] = []
    for e in feed.entries:
        title = getattr(e, "title", "") or ""
        summary = getattr(e, "summary", "") or getattr(e, "description", "") or ""
        link = getattr(e, "link", "") or ""

        if SAFETY_REGEX.search(title) or SAFETY_REGEX.search(summary):
            raw_items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published": getattr(e, "published", "") or getattr(e, "pubDate", "") or "",
            })

    # load cache and current items
    cache = load_json(CACHE_PATH, default={})
    items = load_json(ITEMS_PATH, default=[])
    if not isinstance(items, list):
        items = []

    # index by id
    idx: Dict[str, Dict[str, Any]] = {it.get("id"): it for it in items if isinstance(it, dict) and it.get("id")}

    new_count = 0
    upd_count = 0
    new_cache: Dict[str, str] = {}

    for raw in raw_items:
        url = raw.get("link") or ""
        item_id = fixed_id_from_url(url)
        raw_hash = hash_raw(raw)
        new_cache[item_id] = raw_hash

        prev_hash = cache.get(item_id)
        changed = (prev_hash != raw_hash)

        if item_id not in idx:
            auto = map_to_item(raw)
            idx[item_id] = auto
            new_count += 1
        else:
            if changed:
                auto = map_to_item(raw)
                idx[item_id] = safe_merge(idx[item_id], auto)
                upd_count += 1

    # write back
    out_items = list(idx.values())
    save_json(ITEMS_PATH, out_items)
    save_json(CACHE_PATH, new_cache)

    print(f"Fetched: {len(raw_items)}")
    print(f"New: {new_count}, Updated: {upd_count}")
    print(f"Wrote: {ITEMS_PATH}")
    print(f"Wrote: {CACHE_PATH}")


if __name__ == "__main__":
    main()
