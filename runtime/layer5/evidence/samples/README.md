# Sample evidence payloads (v1)

`example_bundle.json` illustrates `layer5.evidence_bundle.v1` (strict schema: `../evidence_bundle.v1.schema.json`). Values are illustrative except snippet shape, which matches the checked-in golden fixture.

Validate:

```bash
python3 -c "import json; from runtime.layer5.evidence.schema_validate import validate_evidence_bundle_dict; validate_evidence_bundle_dict(json.load(open('runtime/layer5/evidence/samples/example_bundle.json')))"
```

(Run from repo root with `PYTHONPATH=.`)
