#!/bin/bash
# Script to run periodic backup from H100 to local machine using Unison

# Set up logging
LOG_DIR="/root/H100Backups/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backup-$(date +%Y%m%d-%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "H100 Backup Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Set Unison directory to use local profile with excludes
# This ensures we use the profile in /root/H100Backups/.unison and stores archives there
export UNISON="/root/H100Backups/.unison"

# Clean up stale temporary files (optimizing space) - Recursive
echo "Cleaning up stale Unison temp files..." | tee -a "$LOG_FILE"
find /root/H100Backups -name ".unison.*.unison.tmp" -type d -print0 | xargs -0 rm -rf

# Run Unison sync
/usr/bin/unison h100-backup -ui text 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

# Retry logic for corruption/inconsistent state (Exit Code 3)
if [ $EXIT_CODE -eq 3 ]; then
    echo "WARNING: Sync failed (likely inconsistent state). Retrying with -ignorearchives (Sync from Scratch)..." | tee -a "$LOG_FILE"
    
    # -ignorearchives treats the archives as empty, forcing a fresh comparison/sync
    # This solves 'Internal error: On-disk archives are not identical' and 'Archive missing'
    /usr/bin/unison h100-backup -ui text -ignorearchives 2>&1 | tee -a "$LOG_FILE"
    EXIT_CODE=${PIPESTATUS[0]}
fi

echo "========================================" | tee -a "$LOG_FILE"
echo "H100 Backup Completed: $(date)" | tee -a "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "backup-*.log" -mtime +30 -delete

exit $EXIT_CODE
