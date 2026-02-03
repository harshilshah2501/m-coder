# V15 Training - Quick Reference Guide

**Status**: 🚀 Training in progress  
**Expected Completion**: 4-6 hours from start

---

## 📊 Monitor Training Progress

### View Live Logs
```bash
cd ~/Harshil-PoCs/RAG-Datastore/evaluation/finetuning
tail -f training_v15_optimized.log
```

### Check Last 50 Lines
```bash
tail -50 evaluation/finetuning/training_v15_optimized.log
```

### Search for Specific Metrics
```bash
grep "loss\|eval_loss\|accuracy" evaluation/finetuning/training_v15_optimized.log
```

---

## 🔍 Check Training Status

### Is Training Running?
```bash
ps aux | grep -E "train_v15_balanced|python.*finetuning" | grep -v grep
```

### Check GPU Usage
```bash
nvidia-smi
```

### Check Memory Usage
```bash
free -h
```

---

## 🛑 If You Need to Stop Training

### Graceful Stop
```bash
pkill -f "train_v15_balanced.py"
```

### Force Stop
```bash
pkill -9 -f "train_v15_balanced.py"
```

---

## ✅ After Training Completes

### 1. Merge Model
```bash
cd evaluation/finetuning
python3 merge_v15_model.py
```

### 2. Test Inference
```bash
python3 test_v15_inference.py
```

### 3. Deploy vLLM
```bash
source ~/Harshil-PoCs/Finetuning/venv-vllm/bin/activate
cd evaluation/finetuning
python3 -m vllm.entrypoints.openai.api_server \
  --model ./finetuning_output/motadata-coder-v15-merged \
  --served-model-name motadata-coder \
  --host 0.0.0.0 --port 8000
```

### 4. Run Regression Tests
```bash
python3 test_v15_inference.py
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `v15_balanced.jsonl` | Training dataset (2,599 examples) |
| `training_v15_optimized.log` | Main training log |
| `training_v15_nohup.log` | Background process log |
| `finetuning_output/checkpoint-v15` | Training checkpoints |
| `finetuning_output/motadata-coder-v15` | Final model (before merge) |
| `finetuning_output/motadata-coder-v15-merged` | Final merged model |

---

## 🎯 Key Metrics to Watch

- **Training Loss**: Should decrease over time
- **Validation Loss**: Should decrease and stabilize
- **Learning Rate**: 2e-4 (constant)
- **Batch Size**: 16 (effective)
- **Steps/Epoch**: ~309 steps per epoch

---

## 💡 Troubleshooting

### Training Too Slow?
- Check GPU usage: `nvidia-smi`
- Check memory: `free -h`
- Verify batch size in logs

### Training Crashed?
- Check logs: `tail -100 training_v15_optimized.log`
- Check disk space: `df -h`
- Check GPU memory: `nvidia-smi`

### Model Not Found After Training?
- Check: `ls -la finetuning_output/`
- Verify merge script ran: `python3 merge_v15_model.py`

---

**Training started with verified dataset quality!** ✅

