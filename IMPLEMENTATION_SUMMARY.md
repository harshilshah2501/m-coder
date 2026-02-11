# Motadata AI Services - Implementation Summary

**Last Updated**: January 5, 2026

## Overview

Implemented a complete production-ready orchestration system with:
1. **Version-agnostic model naming** - Model name is `motadata-coder` (without version suffix)
2. **Systemd service management** - Orchestrator runs as a managed systemd service
3. **Passwordless sudo authentication** - SSH key-based authentication for secure service management

## Problem Solved
- **Before**: Model name mismatch between vLLM (`motadata-coder-v16`) and RAG API/Coder Agent (`motadata-coder`)
- **After**: All services use the same version-agnostic name `motadata-coder`
- **Service Management**: Manual script execution → Systemd service with auto-start on boot

## Changes Made

### 1. Configuration Files

#### `.config/config.yaml`
- Added `model_name: motadata-coder` to `services.vllm` section
- This is the canonical version-agnostic model name

#### `.config/.env.example`
- Added `VLLM_MODEL_NAME=motadata-coder` (version-agnostic)
- Changed `MODEL_VERSION=v16` (version-specific, for reference only)
- Clear comments explaining the distinction

### 2. Code Changes

#### `runtime/rag/src/api/rag_api.py`
```python
# OLD: VLLM_MODEL = os.getenv("VLLM_MODEL", "motadata-coder")
# NEW: VLLM_MODEL = os.getenv("VLLM_MODEL_NAME", "motadata-coder")
```
- Reads from `VLLM_MODEL_NAME` environment variable
- Falls back to `motadata-coder` if not set

#### `runtime/rag/src/orchestrator/agents/coder_agent.py`
```python
# OLD: self.model = "motadata-coder"
# NEW: self.model = os.getenv("VLLM_MODEL_NAME", "motadata-coder")
```
- Reads from `VLLM_MODEL_NAME` environment variable
- Falls back to `motadata-coder` if not set

### 3. Orchestrator Script

#### `runtime/rag/scripts/orchestrator_unified.sh`
- Added `VLLM_MODEL_NAME="motadata-coder"` variable
- Updated vLLM startup: `--served-model-name $VLLM_MODEL_NAME`
- Updated RAG API startup: `env VLLM_MODEL_NAME="$VLLM_MODEL_NAME" ...`

## How It Works

1. **Orchestrator** defines `VLLM_MODEL_NAME="motadata-coder"`
2. **vLLM** starts with `--served-model-name motadata-coder`
3. **RAG API** receives `VLLM_MODEL_NAME` env var and uses it
4. **Coder Agent** reads `VLLM_MODEL_NAME` env var and uses it
5. All services request model `motadata-coder` from vLLM

## Upgrading to New Versions

To upgrade to a new model version (e.g., v17):

1. Update `MODEL_PATH` in orchestrator script
2. Update `MODEL_VERSION` in `.env.example` (for reference)
3. **No code changes needed** - model name stays `motadata-coder`

## Testing

Verify the setup:
```bash
# Check vLLM is serving the correct model
curl http://localhost:8000/v1/models

# Check RAG API health
curl http://localhost:8081/health

# Test a request
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "motadata-coder", "messages": [{"role": "user", "content": "test"}]}'
```

## 4. Systemd Service Management

### Service Configuration
- **Service File**: `/etc/systemd/system/motadata-orchestrator.service`
- **Service Name**: `motadata-orchestrator`
- **User**: `harshil` (with passwordless sudo via sudoers)
- **Auto-start**: Enabled (starts automatically on system boot)

### Sudoers Configuration
- **File**: `/etc/sudoers.d/motadata-orchestrator`
- **Configuration**: Allows `harshil` user to run docker-compose without password
- **SSH Key**: `/home/harshil/.ssh/motadata-orchestrator` (ED25519 key pair)

### Service Features
- Automatic restart on failure (RestartSec=10)
- Proper dependency management (requires docker.service)
- Comprehensive logging to systemd journal
- Graceful shutdown with 60-second timeout

## Benefits

✅ **Version-agnostic**: Model name doesn't change with versions
✅ **Centralized**: Version info in config, not hardcoded
✅ **Scalable**: Easy to upgrade models without code changes
✅ **Consistent**: All services use the same naming convention
✅ **Production-ready**: Systemd service with auto-start and monitoring
✅ **Secure**: SSH key-based authentication, no hardcoded passwords
✅ **Reliable**: Automatic restart on failure, proper logging

