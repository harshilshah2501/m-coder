#!/usr/bin/env bash
# Version sync, wheel build, JetBrains plugin build, optional installs.
#
# Usage:
#   ./scripts/motadata_packaging.sh help
#   ./scripts/motadata_packaging.sh show-versions
#   ./scripts/motadata_packaging.sh sync-versions
#   ./scripts/motadata_packaging.sh build-wheel
#   ./scripts/motadata_packaging.sh build-plugin
#   ./scripts/motadata_packaging.sh build-all
#   ./scripts/motadata_packaging.sh install-wheel /path/to/venv
#   ./scripts/motadata_packaging.sh install-plugin   # needs JETBRAINS_PLUGIN_INSTALL_DIR or prints zip path
#
# Versions: edit scripts/motadata_versions.env then sync-versions.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${M_CODER_REPO_ROOT:-$SCRIPT_DIR/..}" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/motadata_versions.env"

info() { echo "[INFO] $*"; }
ok() { echo "[OK]   $*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

cmd_help() {
  sed -n '1,25p' "$0" | tail -n +2
}

cmd_show_versions() {
  echo "Manifest: $SCRIPT_DIR/motadata_versions.env"
  echo "  MOTADATA_CONTEXT_LAYER_VERSION=$MOTADATA_CONTEXT_LAYER_VERSION"
  echo "  MOTADATA_JETBRAINS_PLUGIN_VERSION=$MOTADATA_JETBRAINS_PLUGIN_VERSION"
  echo ""
  echo "Files on disk:"
  grep -E '^\[project\]|^version =|^    <version>' -n "$REPO_ROOT/packaging/motadata-context-layer/pyproject.toml" 2>/dev/null | head -5 || true
  grep -E '^version =|^\s*<version>' "$REPO_ROOT/jetbrains-plugin/build.gradle.kts" "$REPO_ROOT/jetbrains-plugin/src/main/resources/META-INF/plugin.xml" 2>/dev/null || true
}

cmd_sync_versions() {
  require_cmd python3
  export M_CODER_REPO_ROOT="$REPO_ROOT"
  export MOTADATA_CONTEXT_LAYER_VERSION MOTADATA_JETBRAINS_PLUGIN_VERSION
  python3 "$SCRIPT_DIR/motadata_apply_versions.py"
}

cmd_build_wheel() {
  require_cmd python3
  local pkg="$REPO_ROOT/packaging/motadata-context-layer"
  local venv="$pkg/.venv-build-packaging"
  info "Building wheel under $pkg (isolated venv: $venv)"
  python3 -m venv "$venv"
  # shellcheck source=/dev/null
  source "$venv/bin/activate"
  pip install -q --upgrade pip build
  ( cd "$pkg" && python -m build --wheel -o dist )
  ls -la "$pkg"/dist/motadata_context_layer-*.whl
  ok "Wheel built"
}

cmd_build_plugin() {
  require_cmd java
  ( cd "$REPO_ROOT/jetbrains-plugin" && ./gradlew --no-daemon buildPlugin )
  ls -la "$REPO_ROOT/jetbrains-plugin/build/distributions"/*.zip
  ok "Plugin zip built"
}

cmd_build_all() {
  cmd_sync_versions
  cmd_build_wheel
  cmd_build_plugin
}

cmd_install_wheel() {
  local venv="${1:-${MOTADATA_CONTEXT_LAYER_VENV:-}}"
  [[ -n "$venv" ]] || fail "Usage: $0 install-wheel /path/to/venv  (or set MOTADATA_CONTEXT_LAYER_VENV)"
  [[ -x "$venv/bin/pip" ]] || fail "Not a Python venv with pip: $venv"
  local wheel
  wheel="$(ls -1 "$REPO_ROOT/packaging/motadata-context-layer/dist"/motadata_context_layer-*.whl 2>/dev/null | tail -1)"
  [[ -f "$wheel" ]] || fail "No wheel in packaging/motadata-context-layer/dist — run build-wheel first"
  "$venv/bin/pip" install -U "$wheel"
  ok "Installed $wheel into $venv (use CONTEXT_LAYER_LAUNCH_MODE=wheel MOTADATA_CONTEXT_LAYER_VENV=$venv with wsl_plugin_mvp_stack.sh)"
}

cmd_install_plugin() {
  local zip="${1:-}"
  if [[ -z "$zip" ]]; then
    zip="$(ls -1 "$REPO_ROOT/jetbrains-plugin/build/distributions"/*.zip 2>/dev/null | tail -1)"
  fi
  [[ -f "$zip" ]] || fail "No plugin zip — run build-plugin first (or pass path to .zip)"
  local dest="${JETBRAINS_PLUGIN_INSTALL_DIR:-}"
  if [[ -z "$dest" ]]; then
    echo ""
    ok "Built plugin archive:"
    echo "  $zip"
    echo ""
    echo "Install manually: IDE → Settings → Plugins → ⚙ → Install Plugin from Disk… → select the zip."
    echo ""
    echo "Or set JETBRAINS_PLUGIN_INSTALL_DIR to your IDE plugins folder and re-run:"
    echo "  export JETBRAINS_PLUGIN_INSTALL_DIR=\"\$HOME/.local/share/JetBrains/IntelliJIdea2025.3/plugins\""
    echo "  (path varies by IDE edition, version, and Toolbox vs standalone)"
    echo "  $0 install-plugin"
    return 0
  fi
  mkdir -p "$dest"
  unzip -o -q "$zip" -d "$dest"
  ok "Extracted into $dest — restart the IDE to load the plugin."
}

case "${1:-help}" in
  help|-h|--help) cmd_help ;;
  show-versions) cmd_show_versions ;;
  sync-versions) cmd_sync_versions ;;
  build-wheel) cmd_build_wheel ;;
  build-plugin) cmd_build_plugin ;;
  build-all) cmd_build_all ;;
  install-wheel) cmd_install_wheel "${2:-}" ;;
  install-plugin) cmd_install_plugin "${2:-}" ;;
  *) fail "Unknown command: ${1:-} (try: $0 help)" ;;
esac
