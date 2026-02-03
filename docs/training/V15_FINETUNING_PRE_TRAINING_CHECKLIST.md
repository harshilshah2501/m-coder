# V15 Fine-tuning Pre-Training Checklist

**Date**: 2025-12-31  
**Status**: ⚠️ **CRITICAL ISSUE IDENTIFIED AND FIXED**

---

## 🔴 Root Cause of OOM Error

**Problem**: Training crashed with `CUDA out of memory` at epoch 1 evaluation (step 309/1545)
- GPU had 78.28 GB in use out of 79.18 GB total
- vLLM service (motadata-coder) was still running in background
- Service was consuming ~17.9 GB of GPU memory

**Solution**: Stop vLLM service BEFORE starting fine-tuning

---

## ✅ Pre-Training Verification Checklist

### 1. Stop vLLM Service (CRITICAL)
```bash
# Check if service is running
systemctl status motadata-coder

# Stop the service
sudo systemctl stop motadata-coder

# Disable auto-start
sudo systemctl disable motadata-coder

# Verify it's stopped
systemctl status motadata-coder
# Should show: inactive (dead)
```

**Status**: ❌ **NOT DONE** - Service is currently ACTIVE and running

### 2. Verify Finetuning Virtual Environment
```bash
# Check venv exists
ls -la ~/Harshil-PoCs/Finetuning/venv/bin/python

# Verify it's the correct Python
~/Harshil-PoCs/Finetuning/venv/bin/python --version
```

**Status**: ✅ **VERIFIED** - venv exists and is ready

### 3. Verify vLLM Virtual Environment (for later deployment)
```bash
# Check venv-vllm exists
ls -la ~/Harshil-PoCs/Finetuning/venv-vllm/bin/python

# Verify it's the correct Python
~/Harshil-PoCs/Finetuning/venv-vllm/bin/python --version
```

**Status**: ✅ **VERIFIED** - venv-vllm exists and is ready

---

## 🚀 Next Steps

1. **STOP vLLM SERVICE** (MUST DO FIRST)
2. Verify GPU memory is freed (should have ~60+ GB free)
3. Run training with correct venv
4. Monitor training progress
5. After training completes, restart vLLM with venv-vllm

---

## 📋 Training Command (After Service Stopped)

```bash
cd ~/Harshil-PoCs/RAG-Datastore
~/Harshil-PoCs/Finetuning/venv/bin/python \
  evaluation/finetuning/train_v15_balanced.py
```

---

**CRITICAL**: Do NOT proceed with training until vLLM service is stopped!

