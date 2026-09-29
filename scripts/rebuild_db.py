#!/usr/bin/env python3
"""Rebuild corpus.db from items.jsonl (append-only source of truth) + briefs/."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "items.jsonl"
DB = ROOT / "corpus.db"
BRIEFS = ROOT / "briefs"


def main() -> None:
    items = []
    if JSONL.exists():
        with JSONL.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))

    if DB.exists():
        DB.unlink()

    con = sqlite3.connect(DB)
    con.executescript(
        """
        CREATE TABLE items (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            urls TEXT,
            why_it_matters TEXT,
            credibility TEXT,
            credibility_note TEXT,
            weight TEXT,
            theme TEXT,
            tags TEXT,
            source_type TEXT,
            notes TEXT
        );
        CREATE TABLE briefs (
            date TEXT PRIMARY KEY,
            theme TEXT,
            markdown_path TEXT
        );
        CREATE VIRTUAL TABLE items_fts USING fts5(
            title,
            why_it_matters,
            tags,
            theme,
            content='items',
            content_rowid='rowid'
        );
        CREATE INDEX idx_items_date ON items(date);
        CREATE INDEX idx_items_url ON items(url);
        CREATE INDEX idx_items_weight ON items(weight);
        """
    )

    for it in items:
        con.execute(
            """
            INSERT INTO items (
                id, date, title, url, urls, why_it_matters, credibility,
                credibility_note, weight, theme, tags, source_type, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                it["id"],
                it["date"],
                it["title"],
                it.get("url") or "",
                json.dumps(it.get("urls") or [], ensure_ascii=False),
                it.get("why_it_matters") or "",
                it.get("credibility") or "",
                it.get("credibility_note") or "",
                it.get("weight") or "",
                it.get("theme") or "",
                json.dumps(it.get("tags") or [], ensure_ascii=False),
                it.get("source_type") or "",
                it.get("notes") or "",
            ),
        )

    # FTS sync from content table
    con.execute(
        """
        INSERT INTO items_fts(rowid, title, why_it_matters, tags, theme)
        SELECT rowid, title, why_it_matters, tags, theme FROM items
        """
    )

    themes_by_date = {}
    for it in items:
        themes_by_date.setdefault(it["date"], it.get("theme") or "")

    for md in sorted(BRIEFS.glob("*.md")):
        date = md.stem
        theme = themes_by_date.get(date, "")
        # try to read theme from first lines if missing
        if not theme:
            text = md.read_text(errors="ignore")
            for line in text.splitlines()[:8]:
                if line.lower().startswith("theme:"):
                    theme = line.split(":", 1)[1].strip()
                    break
        con.execute(
            "INSERT OR REPLACE INTO briefs(date, theme, markdown_path) VALUES (?,?,?)",
            (date, theme, str(md.relative_to(ROOT))),
        )

    con.commit()
    n = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    b = con.execute("SELECT COUNT(*) FROM briefs").fetchone()[0]
    con.close()
    print(f"Rebuilt {DB} — {n} items, {b} briefs (from {JSONL.name})")


if __name__ == "__main__":
    main()
