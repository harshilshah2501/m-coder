#!/bin/bash
#
# Create Local Backup of V16.2 (120 GB)
# Backs up everything except venv, .cache, __pycache__, etc.
#

set -e

PROJECT_ROOT="/home/harshil/Harshil-PoCs"
LOCAL_BACKUP_PATH="${1:-/backup/motadata-v16.2-complete}"

echo "================================================================================"
echo "V16.2 LOCAL BACKUP"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Backup Configuration:"
echo "  Source: $PROJECT_ROOT"
echo "  Destination: $LOCAL_BACKUP_PATH"
echo ""

# Check if destination exists and has space
if [ ! -d "$LOCAL_BACKUP_PATH" ]; then
    echo "Creating backup directory..."
    mkdir -p "$LOCAL_BACKUP_PATH"
fi

# Check available space
AVAILABLE_SPACE=$(df "$LOCAL_BACKUP_PATH" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=$((120 * 1024 * 1024))  # 120 GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "❌ ERROR: Not enough space!"
    echo "  Available: $(numfmt --to=iec $((AVAILABLE_SPACE * 1024)) 2>/dev/null || echo $AVAILABLE_SPACE KB)"
    echo "  Required: 120 GB"
    exit 1
fi

echo "✓ Sufficient space available"
echo ""
echo "================================================================================"
echo "BACKING UP COMPONENTS"
echo "================================================================================"

# Function to backup with progress
backup_dir() {
    local src="$1"
    local dst="$2"
    local name="$3"
    
    if [ ! -d "$src" ]; then
        echo "⚠ Skipping $name (not found)"
        return
    fi
    
    echo ""
    echo "Backing up $name..."
    rsync -av --progress "$src/" "$dst/" \
        --exclude="venv" \
        --exclude="env" \
        --exclude=".venv" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".cache" \
        --exclude=".pytest_cache" \
        --exclude="*.egg-info" \
        --exclude=".git" \
        --exclude="model-backups" \
        2>&1 | tail -20
}

# Backup each component
backup_dir "$PROJECT_ROOT/models" "$LOCAL_BACKUP_PATH/models" "models (56 GB)"
backup_dir "$PROJECT_ROOT/training" "$LOCAL_BACKUP_PATH/training" "training (1.3 GB)"
backup_dir "$PROJECT_ROOT/datasets" "$LOCAL_BACKUP_PATH/datasets" "datasets (175 MB)"
backup_dir "$PROJECT_ROOT/evaluation" "$LOCAL_BACKUP_PATH/evaluation" "evaluation (6.3 MB)"
backup_dir "$PROJECT_ROOT/rag" "$LOCAL_BACKUP_PATH/rag" "rag (2.2 MB)"
backup_dir "$PROJECT_ROOT/docs" "$LOCAL_BACKUP_PATH/docs" "docs (15 MB)"
backup_dir "$PROJECT_ROOT/scripts" "$LOCAL_BACKUP_PATH/scripts" "scripts (64 KB)"
backup_dir "$PROJECT_ROOT/logs" "$LOCAL_BACKUP_PATH/logs" "logs (300 KB)"
backup_dir "$PROJECT_ROOT/agents" "$LOCAL_BACKUP_PATH/agents" "agents (16 KB)"

# Backup root markdown files
echo ""
echo "Backing up root documentation..."
cp "$PROJECT_ROOT"/*.md "$LOCAL_BACKUP_PATH/" 2>/dev/null || true

# Create backup manifest
echo ""
echo "Creating backup manifest..."
cat > "$LOCAL_BACKUP_PATH/BACKUP_MANIFEST.txt" << EOF
V16.2 Complete Local Backup
============================
Created: $(date '+%Y-%m-%d %H:%M:%S')
Source: $PROJECT_ROOT
Destination: $LOCAL_BACKUP_PATH

Contents:
  ✓ models/                 (56 GB)
  ✓ training/               (1.3 GB)
  ✓ datasets/               (175 MB)
  ✓ evaluation/             (6.3 MB)
  ✓ rag/                    (2.2 MB)
  ✓ docs/                   (15 MB)
  ✓ scripts/                (64 KB)
  ✓ logs/                   (300 KB)
  ✓ agents/                 (16 KB)
  ✓ *.md files              (100 KB)

Excluded:
  ✗ venv/                   (17 GB)
  ✗ model-backups/          (15 GB)
  ✗ __pycache__/
  ✗ .cache/
  ✗ *.pyc

Total Size: ~120 GB

To restore:
  rsync -av "$LOCAL_BACKUP_PATH/" /path/to/restore/

Verification:
  du -sh "$LOCAL_BACKUP_PATH"
EOF

echo "✓ Created BACKUP_MANIFEST.txt"

# Calculate total size
echo ""
echo "================================================================================"
echo "✅ LOCAL BACKUP COMPLETE"
echo "================================================================================"
TOTAL_SIZE=$(du -sh "$LOCAL_BACKUP_PATH" | awk '{print $1}')
echo ""
echo "Backup Summary:"
echo "  Location: $LOCAL_BACKUP_PATH"
echo "  Total Size: $TOTAL_SIZE"
echo "  Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "To verify backup integrity:"
echo "  du -sh $LOCAL_BACKUP_PATH"
echo ""

