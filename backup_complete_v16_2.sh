#!/bin/bash
#
# Complete V16.2 Backup Script (Option D - Hybrid)
# Backs up everything except venv, .cache, __pycache__, etc.
#
# Tiers:
#   1. Hugging Face (27.5 GB model)
#   2. GitHub (50 MB code)
#   3. Local backup (120 GB everything)
#

set -e

PROJECT_ROOT="/home/harshil/Harshil-PoCs"
HF_TOKEN="${HF_TOKEN:-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}"
HF_REPO="harshilshah25/motadata-coder-Qwen2.5-Coder-14B-Instruct-finetuned-v16.2"
GITHUB_REPO="harshilshah25/motadata-coder-v16.2"
LOCAL_BACKUP_PATH="${LOCAL_BACKUP_PATH:-/backup/motadata-v16.2-complete}"

echo "================================================================================"
echo "V16.2 COMPLETE BACKUP - OPTION D (HYBRID)"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Backup Configuration:"
echo "  Project Root: $PROJECT_ROOT"
echo "  HF Repo: $HF_REPO"
echo "  GitHub Repo: $GITHUB_REPO"
echo "  Local Backup: $LOCAL_BACKUP_PATH"
echo ""
echo "================================================================================"

# Tier 1: Hugging Face
echo ""
echo "TIER 1: UPLOADING TO HUGGING FACE (27.5 GB)"
echo "================================================================================"
python3 "$PROJECT_ROOT/backup_v16_2_to_hf.py"

# Tier 2: GitHub
echo ""
echo "TIER 2: PUSHING TO GITHUB (50 MB)"
echo "================================================================================"
echo "Note: GitHub setup requires manual steps:"
echo "  1. Create repo: $GITHUB_REPO"
echo "  2. Run: cd $PROJECT_ROOT && git init"
echo "  3. Add remote: git remote add origin https://github.com/$GITHUB_REPO.git"
echo "  4. Create .gitignore and push"
echo ""
echo "Skipping GitHub for now - requires manual setup"

# Tier 3: Local Backup
echo ""
echo "TIER 3: CREATING LOCAL BACKUP (120 GB)"
echo "================================================================================"
mkdir -p "$LOCAL_BACKUP_PATH"

echo "Backing up models/ (56 GB)..."
rsync -av --progress "$PROJECT_ROOT/models/" "$LOCAL_BACKUP_PATH/models/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up training/ (1.3 GB)..."
rsync -av --progress "$PROJECT_ROOT/training/" "$LOCAL_BACKUP_PATH/training/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up datasets/ (175 MB)..."
rsync -av --progress "$PROJECT_ROOT/datasets/" "$LOCAL_BACKUP_PATH/datasets/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up evaluation/ (6.3 MB)..."
rsync -av --progress "$PROJECT_ROOT/evaluation/" "$LOCAL_BACKUP_PATH/evaluation/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up rag/ (2.2 MB)..."
rsync -av --progress "$PROJECT_ROOT/rag/" "$LOCAL_BACKUP_PATH/rag/" \
  --exclude="venv" --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up docs/ (15 MB)..."
rsync -av --progress "$PROJECT_ROOT/docs/" "$LOCAL_BACKUP_PATH/docs/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up scripts/ (64 KB)..."
rsync -av --progress "$PROJECT_ROOT/scripts/" "$LOCAL_BACKUP_PATH/scripts/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up logs/ (300 KB)..."
rsync -av --progress "$PROJECT_ROOT/logs/" "$LOCAL_BACKUP_PATH/logs/" \
  --exclude="*.pyc" --exclude="__pycache__" --exclude=".cache"

echo "Backing up root markdown files..."
rsync -av --progress "$PROJECT_ROOT/"*.md "$LOCAL_BACKUP_PATH/" 2>/dev/null || true

echo ""
echo "================================================================================"
echo "✅ BACKUP COMPLETE"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ Tier 1 (HF): Model uploaded to $HF_REPO"
echo "  ⏳ Tier 2 (GitHub): Manual setup required"
echo "  ✓ Tier 3 (Local): Backup created at $LOCAL_BACKUP_PATH"
echo ""
echo "Total backup size: ~120 GB"
echo "Backup location: $LOCAL_BACKUP_PATH"
echo ""

