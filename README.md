# Agentic & AI interface corpus

**Live on GitHub:** https://github.com/btmerr/agentic-interface-corpus

Curated archive of Brian Merritt’s weekday **Agentic & AI interface** briefs (coding-harness / agent UX focus). Updated automatically after each weekday morning brief.

## Layout

```
agentic-interface-corpus/
  README.md          — this file
  schema.md          — field definitions
  items.jsonl        — append-only source of truth (one JSON object per line)
  corpus.db          — SQLite mirror + FTS5 (rebuildable)
  INDEX.md           — human-scannable index by theme tags
  briefs/YYYY-MM-DD.md
  scripts/rebuild_db.py
  scripts/append_item.py
```

## Query

### SQLite / FTS

```bash
sqlite3 corpus.db "SELECT date, title, weight FROM items ORDER BY date DESC LIMIT 20;"

sqlite3 corpus.db "SELECT title, url FROM items_fts WHERE items_fts MATCH 'approval OR interrupt' LIMIT 20;"

sqlite3 corpus.db "SELECT date, title FROM items WHERE tags LIKE '%\"plan\"%' ORDER BY date;"
```

### JSONL

```bash
jq -c 'select(.weight=="high")' items.jsonl
jq -c 'select(.tags|index("canvas"))' items.jsonl
```

### Rebuild DB from JSONL

```bash
python3 scripts/rebuild_db.py
```

## Morning routine — append today’s brief items

After delivering the weekday brief, for each item:

```bash
python3 scripts/append_item.py \
  --date YYYY-MM-DD \
  --title "Exact title" \
  --url "https://..." \
  --why "Why it matters for the harness UI." \
  --credibility High \
  --credibility-note "primary product / research / …" \
  --weight high \
  --theme "day theme" \
  --tags '["plan","approval"]' \
  --source-type product
```

Or pass a full object:

```bash
python3 scripts/append_item.py --json '{"id":"...","date":"YYYY-MM-DD","title":"...","url":"...","urls":[],"why_it_matters":"...","credibility":"High","credibility_note":"...","weight":"high","theme":"...","tags":["harness"],"source_type":"product","notes":""}'
```

Also archive the delivered brief text:

```bash
# write briefs/YYYY-MM-DD.md then refresh briefs table
python3 scripts/rebuild_db.py
```

`append_item.py` is **idempotent by normalized URL** (strip trailing slash, lowercase host). Re-running the same URL updates the row and notes later re-mentions.

Alternative: append a JSON line to `items.jsonl` by hand, then `python3 scripts/rebuild_db.py`.

## Provenance

- **2026-09-07 … 2026-09-14** (plus 09-08..09-11 weekday runs): full brief text recovered from parent transcript / store send-messages; items parsed with credibility calls.
- **2026-09-15 … 2026-09-24**: local transcript snapshot ended at 2026-09-14; items reconstructed from memory-log summaries + primary URLs (web lookup when title uniquely identified a public page). Stub brief files note reconstruction.
