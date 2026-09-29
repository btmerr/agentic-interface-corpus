#!/usr/bin/env python3
"""Append one item to items.jsonl and upsert corpus.db (idempotent by normalized URL)."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "items.jsonl"
DB = ROOT / "corpus.db"


def norm_url(u: str | None) -> str | None:
    if not u:
        return None
    u = u.strip().rstrip(".,);]")
    p = urlparse(u)
    if not p.scheme or not p.netloc:
        return None
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or ""
    return urlunparse((p.scheme.lower(), host, path, "", p.query, ""))


def slugify(title: str, date: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    return f"{date}-{s}"


def load_jsonl() -> list[dict]:
    items = []
    if JSONL.exists():
        with JSONL.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    return items


def write_jsonl(items: list[dict]) -> None:
    with JSONL.open("w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def upsert_db(item: dict) -> None:
    if not DB.exists():
        # lazy rebuild
        from rebuild_db import main as rebuild

        rebuild()
        return

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    nu = norm_url(item.get("url"))
    existing_id = None
    if nu:
        for row in con.execute("SELECT id, url FROM items"):
            if norm_url(row["url"]) == nu:
                existing_id = row["id"]
                break

    payload = (
        item["id"] if not existing_id else existing_id,
        item["date"],
        item["title"],
        item.get("url") or "",
        json.dumps(item.get("urls") or [], ensure_ascii=False),
        item.get("why_it_matters") or "",
        item.get("credibility") or "",
        item.get("credibility_note") or "",
        item.get("weight") or "",
        item.get("theme") or "",
        json.dumps(item.get("tags") or [], ensure_ascii=False),
        item.get("source_type") or "",
        item.get("notes") or "",
    )

    if existing_id:
        con.execute("DELETE FROM items_fts WHERE rowid = (SELECT rowid FROM items WHERE id=?)", (existing_id,))
        con.execute(
            """
            UPDATE items SET
                id=?, date=?, title=?, url=?, urls=?, why_it_matters=?, credibility=?,
                credibility_note=?, weight=?, theme=?, tags=?, source_type=?, notes=?
            WHERE id=?
            """,
            payload + (existing_id,),
        )
        item["id"] = existing_id
    else:
        con.execute(
            """
            INSERT INTO items (
                id, date, title, url, urls, why_it_matters, credibility,
                credibility_note, weight, theme, tags, source_type, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            payload,
        )

    con.execute(
        """
        INSERT INTO items_fts(rowid, title, why_it_matters, tags, theme)
        SELECT rowid, title, why_it_matters, tags, theme FROM items WHERE id=?
        """,
        (item["id"],),
    )
    con.commit()
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Append/upsert one research item into the corpus")
    ap.add_argument("--json", help="Inline JSON object for the item")
    ap.add_argument("--file", help="Path to a JSON file for the item")
    ap.add_argument("--date", help="YYYY-MM-DD")
    ap.add_argument("--title")
    ap.add_argument("--url", default="")
    ap.add_argument("--urls", default="[]", help="JSON array of secondary URLs")
    ap.add_argument("--why", dest="why_it_matters", default="")
    ap.add_argument("--credibility", default="Medium")
    ap.add_argument("--credibility-note", default="")
    ap.add_argument("--weight", default="medium")
    ap.add_argument("--theme", default="")
    ap.add_argument("--tags", default="[]", help="JSON array of tags")
    ap.add_argument("--source-type", default="product")
    ap.add_argument("--notes", default="")
    ap.add_argument("--id", default="")
    args = ap.parse_args()

    if args.json:
        item = json.loads(args.json)
    elif args.file:
        item = json.loads(Path(args.file).read_text())
    elif args.date and args.title:
        item = {
            "date": args.date,
            "title": args.title,
            "url": args.url,
            "urls": json.loads(args.urls),
            "why_it_matters": args.why_it_matters,
            "credibility": args.credibility,
            "credibility_note": args.credibility_note,
            "weight": args.weight,
            "theme": args.theme,
            "tags": json.loads(args.tags),
            "source_type": args.source_type,
            "notes": args.notes,
        }
        item["id"] = args.id or slugify(args.title, args.date)
    else:
        ap.error("Provide --json, --file, or --date + --title (+ fields)")

    # normalize required fields
    item.setdefault("urls", [])
    item.setdefault("notes", "")
    item.setdefault("id", slugify(item["title"], item["date"]))

    items = load_jsonl()
    nu = norm_url(item.get("url"))
    replaced = False
    if nu:
        for i, ex in enumerate(items):
            if norm_url(ex.get("url")) == nu:
                # merge secondary urls
                secs = list(ex.get("urls") or [])
                for u in [item.get("url")] + list(item.get("urls") or []):
                    if u and norm_url(u) != nu and u not in secs:
                        secs.append(u)
                merged = {**ex, **item, "id": ex["id"], "urls": secs}
                if item.get("date") and item["date"] != ex.get("date"):
                    note = merged.get("notes") or ""
                    add = f"also in brief {item['date']}"
                    merged["notes"] = (note + "; " + add).strip("; ")
                items[i] = merged
                item = merged
                replaced = True
                break
    if not replaced:
        items.append(item)

    write_jsonl(items)
    upsert_db(item)
    action = "updated" if replaced else "appended"
    print(f"{action} id={item['id']} url={item.get('url')!r} (jsonl={len(items)} items)")


if __name__ == "__main__":
    main()
