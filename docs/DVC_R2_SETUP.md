# DVC + Cloudflare R2 (Deferred / Future Use)

**Current prototype/evaluation stage uses local disk only.** See [DVC_ARTIFACTS_README.md](DVC_ARTIFACTS_README.md) for active setup.

The `r2` remote is kept in `.dvc/config` but is **inactive**. Use this doc when you decide to enable cloud backup.

## Prerequisites

- DVC with S3: `pip install 'dvc[s3]'`
- R2 bucket (e.g. `motadataed`) with prefix `dvc`.

## Environment Variables (do not store in Git)

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | R2 API token Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | R2 API token Secret Access Key |
| `AWS_DEFAULT_REGION` | Use `auto` for R2 |
| `AWS_ENDPOINT_URL` | e.g. `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |

## Enabling R2

```bash
# Set env vars, then:
dvc remote default r2
# Or push/pull explicitly: dvc push -r r2 / dvc pull -r r2
```

## Usage when R2 is active

- Push: `dvc push` (or `make dvc-push-checkpoints RUN_ID=...`)
- Pull: `dvc pull` (or `make dvc-pull-checkpoints RUN_ID=...`)
