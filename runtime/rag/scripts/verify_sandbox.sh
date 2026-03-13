#!/bin/bash
# Motadata Sandbox Build & Verification Script
# Purpose: Build Docker image and verify compilation/testing capabilities

set -e

echo "========================================"
echo "Motadata Sandbox Build & Verification"
echo "========================================"

# Navigate to docker directory
cd "$(dirname "$0")"

echo ""
echo "[1/4] Building Motadata Sandbox Docker Image..."
docker-compose build motadata-sandbox

echo ""
echo "[2/4] Creating temporary workspace..."
TEMP_WORKSPACE="/tmp/motadata-workspace-test-$$"
mkdir -p "$TEMP_WORKSPACE"
cp -r docker/motadata-sandbox/test-project/* "$TEMP_WORKSPACE/"

echo ""
echo "[3/4] Testing compilation with 'mvn compile'..."
docker run --rm \
    -v "$TEMP_WORKSPACE:/workspace" \
    -v maven-cache:/root/.m2/repository \
    rag-system_motadata-sandbox \
    bash -c "cd /workspace && mvn clean compile"

echo ""
echo "[4/4] Testing execution with 'mvn test'..."
docker run --rm \
    -v "$TEMP_WORKSPACE:/workspace" \
    -v maven-cache:/root/.m2/repository \
    rag-system_motadata-sandbox \
    bash -c "cd /workspace && mvn test"

echo ""
echo "✅ Sandbox verification complete!"
echo ""
echo "Results:"
echo "  - Docker image: motadata-sandbox (built successfully)"
echo "  - Java compilation: PASSED"
echo "  - Maven test execution: PASSED"
echo "  - Vert.x dependencies: RESOLVED"
echo ""
echo "Cleanup temporary workspace..."
sudo rm -rf "$TEMP_WORKSPACE" 2>/dev/null || rm -rf "$TEMP_WORKSPACE" 2>/dev/null || true

echo ""
echo "Next steps:"
echo "  1. Sandbox is ready for Motadata-Bench task execution"
echo "  2. Start all services: docker-compose up -d"
echo "  3. Check status: docker-compose ps"
echo ""
