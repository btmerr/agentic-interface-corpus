# Item schema

Each line of `items.jsonl` is one JSON object. `corpus.db` mirrors the same fields.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Slug `{date}-{title-slug}` (or uuid). Stable across upserts when URL matches. |
| `date` | string | yes | Brief date `YYYY-MM-DD` (first appearance). Later re-mentions noted in `notes`. |
| `title` | string | yes | Human title as delivered in the brief. |
| `url` | string | yes* | Primary URL. Empty string if unrecovered (`notes` must say so). |
| `urls` | string[] | no | Secondary URLs (docs mirrors, companion posts, repos). |
| `why_it_matters` | string | yes | 1–3 sentences for Brian’s coding-harness interface work. |
| `credibility` | enum | yes | `High` \| `Medium-high` \| `Medium` \| `Medium-low` \| `Low` |
| `credibility_note` | string | no | Short who/what track-record note. |
| `weight` | enum | yes | `high` \| `medium-high` \| `medium` \| `low` — how much attention to give. |
| `theme` | string | no | That day’s cross-cutting theme. |
| `tags` | string[] | yes | Free tags; common: `plan`, `approval`, `canvas`, `fleet`, `protocol`, `harness`, `eval`, `interrupt`, `trace`, `genui`, `pattern`, `oss`, `vendor`. |
| `source_type` | enum | yes | `product` \| `protocol` \| `research` \| `pattern` \| `vendor-post` \| `oss` |
| `notes` | string | no | Recovery notes, later re-mentions, caveats. |

## Deduping

Normalize URL before compare:

1. Lowercase scheme + host
2. Strip leading `www.`
3. Strip trailing `/` on path
4. Drop fragment; keep query string

`scripts/append_item.py` upserts by normalized primary URL (idempotent).

## SQLite

- `items` — same fields; `tags` and `urls` stored as JSON text
- `briefs` — `date`, `theme`, `markdown_path`
- `items_fts` — FTS5 over `title`, `why_it_matters`, `tags`, `theme`

## Briefs table / files

`briefs/YYYY-MM-DD.md` holds archived delivered brief text when recoverable.
Memory-only dates have a stub noting reconstruction.
