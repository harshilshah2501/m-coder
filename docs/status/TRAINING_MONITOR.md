# V16.1 Training Monitoring

## Quick Start

### 1. Attach to Training Screen Session
```bash
screen -r v16_1_training
```

### 2. View Training Logs in Real-Time
```bash
# Option A: From screen session (already attached above)
# Just watch the output

# Option B: Tail the log file
tail -f /home/harshil/Harshil-PoCs/training/checkpoints/v16_1/logs/events.out.tfevents.*

# Option C: Watch training progress
watch -n 5 'tail -20 /home/harshil/Harshil-PoCs/training/checkpoints/v16_1/logs/events.out.tfevents.*'
```

### 3. Monitor GPU Usage
```bash
# Watch GPU memory and utilization
watch -n 2 nvidia-smi

# Or continuous monitoring
nvidia-smi -l 2
```

### 4. Check Checkpoint Progress
```bash
ls -lh /home/harshil/Harshil-PoCs/training/checkpoints/v16_1/
```

### 5. View TensorBoard (Optional)
```bash
# Start TensorBoard
tensorboard --logdir=/home/harshil/Harshil-PoCs/training/checkpoints/v16_1/logs

# Access at: http://localhost:6006
```

## Key Log Locations

| Log Type | Location |
|----------|----------|
| **Training Output** | Screen session: `screen -r v16_1_training` |
| **TensorBoard Events** | `/home/harshil/Harshil-PoCs/training/checkpoints/v16_1/logs/` |
| **Checkpoints** | `/home/harshil/Harshil-PoCs/training/checkpoints/v16_1/` |
| **Final Model** | `/home/harshil/Harshil-PoCs/models/v16_1_finetuned/` |

## Training Details

- **Dataset**: v16_1_surgical.jsonl (3,912 examples)
- **Train Split**: 3,129 examples (80%)
- **Val Split**: 391 examples (10%)
- **Test Split**: 392 examples (10%)
- **Batch Size**: 2
- **Gradient Accumulation**: 4
- **Learning Rate**: 2e-5
- **Epochs**: 3
- **Max Seq Length**: 8192

## Expected Training Time

- **Estimated Duration**: ~4-6 hours (depending on GPU)
- **Checkpoints**: Saved every 100 steps
- **Evaluations**: Every 100 steps

## Detach from Screen (Without Stopping Training)

Press: `Ctrl+A` then `D`

## Reattach to Screen

```bash
screen -r v16_1_training
```

## Kill Training (If Needed)

```bash
# From screen session
Ctrl+C

# Or from outside
screen -S v16_1_training -X quit
```

