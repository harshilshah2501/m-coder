#!/bin/bash
#
# Push V16.2 Code to GitHub
# Backs up training scripts, RAG code, docs, configs
#

set -e

PROJECT_ROOT="/home/harshil/Harshil-PoCs"
GITHUB_REPO="harshilshah25/motadata-coder-v16.2"
GITHUB_URL="https://github.com/$GITHUB_REPO.git"

echo "================================================================================"
echo "V16.2 GITHUB BACKUP"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "GitHub Configuration:"
echo "  Repo: $GITHUB_REPO"
echo "  URL: $GITHUB_URL"
echo ""
echo "================================================================================"

# Check if git is initialized
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo ""
    echo "Initializing git repository..."
    cd "$PROJECT_ROOT"
    git init
    git config user.email "harshil@motadata.com"
    git config user.name "Harshil Shah"
fi

# Create .gitignore if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.gitignore" ]; then
    echo ""
    echo "Creating .gitignore..."
    cat > "$PROJECT_ROOT/.gitignore" << 'EOF'
# Virtual environments
venv/
env/
ENV/
.venv/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db

# Large files (use Git LFS or backup separately)
models/
model-backups/
*.safetensors
*.bin

# Cache
.cache/
.pytest_cache/
.mypy_cache/

# Logs
*.log
logs/

# Temporary
*.tmp
*.temp
.env
.env.local
EOF
    echo "✓ Created .gitignore"
fi

# Add files
echo ""
echo "Adding files to git..."
cd "$PROJECT_ROOT"
git add -A

# Check if there are changes
if git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

# Commit
echo "Committing changes..."
git commit -m "V16.2 Complete Backup - Training, RAG, Evaluation, Docs

- Training scripts and checkpoints
- RAG API and orchestrator
- Evaluation scripts and results
- Complete documentation
- Configuration files
- Utility scripts

Excludes: venv, models, caches, large files"

# Add remote if not exists
if ! git remote | grep -q origin; then
    echo ""
    echo "Adding remote origin..."
    git remote add origin "$GITHUB_URL"
fi

# Push
echo ""
echo "Pushing to GitHub..."
echo "Note: You may need to authenticate with GitHub"
echo "Use: git push -u origin main"
echo ""
echo "To complete the push, run:"
echo "  cd $PROJECT_ROOT"
echo "  git push -u origin main"
echo ""
echo "================================================================================"
echo "✅ GIT SETUP COMPLETE"
echo "================================================================================"

