#!/usr/bin/env bash
#
# Quick monitoring script for V16.1 training
#

echo "================================================================================"
echo "V16.1 TRAINING MONITOR"
echo "================================================================================"
echo ""

# Check screen session
echo "📺 Screen Session Status:"
screen -ls | grep v16_1_training || echo "  ❌ No active session"
echo ""

# Check log file
echo "📝 Latest Training Output:"
if [ -f "/home/harshil/Harshil-PoCs/training/logs/v16_1_training.log" ]; then
    tail -20 /home/harshil/Harshil-PoCs/training/logs/v16_1_training.log
else
    echo "  ⏳ Log file not yet created"
fi
echo ""

# Check GPU
echo "🎮 GPU Status:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,utilization.memory --format=csv,noheader
echo ""

# Check checkpoints
echo "💾 Checkpoints:"
ls -lh /home/harshil/Harshil-PoCs/training/checkpoints/v16_1/ 2>/dev/null | tail -5 || echo "  ⏳ No checkpoints yet"
echo ""

echo "================================================================================"
echo "Commands:"
echo "  Attach to training:  screen -r v16_1_training"
echo "  Detach from screen:  Ctrl+A then D"
echo "  Stop training:       screen -S v16_1_training -X quit"
echo "================================================================================"

