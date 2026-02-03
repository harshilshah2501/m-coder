#!/usr/bin/env bash
#
# V16.1 Training Script
# Train with surgically precise dataset (3,912 examples)
#

set -e

echo "================================================================================"
echo "V16.1 TRAINING - STARTING"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Paths
PROJECT_ROOT="/home/harshil/Harshil-PoCs"
VENV_PATH="$PROJECT_ROOT/venv/training"
# Using FIXED dataset with SEARCH/REPLACE format (was v16_1_splits)
TRAIN_DATA="$PROJECT_ROOT/datasets/v16_1_fixed/train.jsonl"
VAL_DATA="$PROJECT_ROOT/datasets/v16_1_fixed/val.jsonl"
OUTPUT_DIR="$PROJECT_ROOT/models/v16_1_finetuned"
BASE_MODEL="Qwen/Qwen2.5-Coder-14B-Instruct"

# Training parameters (same as V16)
BATCH_SIZE=2
GRADIENT_ACCUM=4
LEARNING_RATE=2e-5
EPOCHS=3
MAX_SEQ_LENGTH=8192
WARMUP_RATIO=0.1

echo "Configuration:"
echo "  Base Model: $BASE_MODEL"
echo "  Train Data: $TRAIN_DATA (3,129 examples)"
echo "  Val Data: $VAL_DATA (391 examples)"
echo "  Output: $OUTPUT_DIR"
echo "  Batch Size: $BATCH_SIZE"
echo "  Gradient Accumulation: $GRADIENT_ACCUM"
echo "  Learning Rate: $LEARNING_RATE"
echo "  Epochs: $EPOCHS"
echo "  Max Seq Length: $MAX_SEQ_LENGTH"
echo ""

# Activate venv
echo "Activating training venv..."
source "$VENV_PATH/bin/activate"

# Verify data files
echo "Verifying data files..."
if [ ! -f "$TRAIN_DATA" ]; then
    echo "ERROR: Training data not found: $TRAIN_DATA"
    exit 1
fi

if [ ! -f "$VAL_DATA" ]; then
    echo "ERROR: Validation data not found: $VAL_DATA"
    exit 1
fi

echo "✓ Training data: $(wc -l < $TRAIN_DATA) lines"
echo "✓ Validation data: $(wc -l < $VAL_DATA) lines"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start training
echo "================================================================================"
echo "STARTING TRAINING"
echo "================================================================================"
echo ""

cd "$PROJECT_ROOT"

python training/src/finetuning/train_v16_1_surgical.py

echo ""
echo "================================================================================"
echo "TRAINING COMPLETE"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Output: $OUTPUT_DIR"
echo "================================================================================"

