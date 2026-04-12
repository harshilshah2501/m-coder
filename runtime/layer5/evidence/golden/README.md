# Golden evidence bundle (v1)

- **`fixture_workspace/`** — tiny checked-in tree indexed for retrieval + evidence.
- **`evidence_bundle.v1.masked.json`** — expected bundle with `canonical_root` and `workspace_identity_hash` cleared (for diff + fingerprint).
- **`evidence_bundle.v1.fingerprint.sha256`** — SHA-256 of `json.dumps(masked_dict, sort_keys=True, separators=(",", ":"))` UTF-8.

**Regenerate** (only when intentionally changing the fixture or contract):

```bash
cd repo_root && PYTHONPATH=. python3 -c "
from pathlib import Path
import json
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.evidence import build_evidence_bundle, SnippetConfig
from runtime.layer5.evidence.fingerprint import masked_bundle_dict, bundle_masked_fingerprint_sha256
from runtime.layer5.evidence.schema_validate import validate_evidence_bundle_dict
from runtime.layer5.workspace.identity import WorkspaceIdentity

root = Path('runtime/layer5/evidence/golden/fixture_workspace').resolve()
root_s = str(root)
ident = WorkspaceIdentity(
    canonical_root=root_s,
    identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
    original_input=root_s,
    path_type='posix',
    is_git_repo=False,
)
idx = build_file_index(ident)
r = retrieve_lexical(idx, 'hello', top_k=1, config=LexicalRetrievalConfig())
b = build_evidence_bundle(r, idx, snippet_config=SnippetConfig(context_lines_before=2, context_lines_after=2))
validate_evidence_bundle_dict(json.loads(b.to_json()))
base = Path('runtime/layer5/evidence/golden')
base.joinpath('evidence_bundle.v1.masked.json').write_text(
    json.dumps(masked_bundle_dict(b), indent=2, sort_keys=True) + chr(10), encoding='utf-8')
base.joinpath('evidence_bundle.v1.fingerprint.sha256').write_text(
    bundle_masked_fingerprint_sha256(b) + chr(10), encoding='utf-8')
print(bundle_masked_fingerprint_sha256(b))
"
```
