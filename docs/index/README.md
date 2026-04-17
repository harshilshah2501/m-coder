# Documentation Index Assets

This directory contains machine-consumable documentation indexing assets.

- `doc_catalog.source.json` - curated source of entries (human-maintained)
- `doc_catalog.json` - generated routing catalog (`docs.catalog.v1`)

Generate/refresh catalog from source:

```bash
python3 runtime/scripts/generate_doc_catalog.py
```

Primary human navigation remains:

- `../NAVIGATION_HUB.md`
- `../MOTADATA_DEMOBOOK.md`
