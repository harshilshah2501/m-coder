#!/usr/bin/env bash
#
# Point mcoder_suite-latest-py3-none-any.whl at the newest concrete wheel in DIR.
# Optional: prune older versioned wheels (defaults to keeping only one).
#
# Usage:
#   bash link_mcoder_suite_latest.sh [--keep N] [--no-prune] DIST_DIR
#
# Examples:
#   bash link_mcoder_suite_latest.sh dist
#   bash link_mcoder_suite_latest.sh --keep 3 ~/motadata-wheel
#
# The stable name is intentional: use the same pip path on WSL every time after
# build or rsync/scp workflow (see README.md).

set -euo pipefail

STABLE_REL="mcoder_suite-latest-py3-none-any.whl"
KEEP=""
NO_PRUNE=0

while [[ $# -gt 0 ]]; do
	case "$1" in
		--keep)
			KEEP="${2:?}"
			shift 2
			;;
		--no-prune)
			NO_PRUNE=1
			shift
			;;
		-h|--help)
			echo "Usage: $(basename "$0") [--keep N] [--no-prune] DIST_DIR"
			echo "  Updates ${STABLE_REL} to the newest mcoder_suite-*-py3-none-any.whl in DIST_DIR."
			echo "  Default: prune older concrete wheels (--keep 1)."
			exit 0
			;;
		--)
			shift
			break
			;;
		-*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
		*)
			break
			;;
	esac
done

if [[ -z "${KEEP:-}" ]]; then
	KEEP="${MCODER_SUITE_WHEEL_KEEP:-1}"
fi

DIST_ARG="${1:?usage: $(basename "$0") [--keep N] [--no-prune] DIST_DIR}"

if [[ $NO_PRUNE -eq 1 ]]; then
	KEEP=999999
fi

DIST_DIR="$(cd "$DIST_ARG" && pwd)"

shopt -s nullglob
vers_files=()
for f in "${DIST_DIR}"/mcoder_suite-*-py3-none-any.whl; do
	[[ "$(basename "$f")" != "$STABLE_REL" ]] || continue
	[[ -f "$f" && ! -L "$f" ]] || continue
	vers_files+=("$f")
done
shopt -u nullglob

if [[ ${#vers_files[@]} -eq 0 ]]; then
	echo "[FAIL] No versioned mcoder_suite-*-py3-none-any.whl in $DIST_DIR" >&2
	exit 1
fi

_mtime_of() {
	stat -c '%Y' "$1" 2>/dev/null || stat -f '%m' "$1"
}

mapfile -t sorted < <(
	for f in "${vers_files[@]}"; do
		printf '%s\t%s\n' "$(_mtime_of "$f")" "$f"
	done | sort -nr | cut -f2-
)
NEWEST="${sorted[0]}"
[[ -n "$NEWEST" && -f "$NEWEST" ]] || { echo "[FAIL] Could not pick newest wheel" >&2; exit 1; }

if [[ "$KEEP" =~ ^[0-9]+$ ]] && [[ "$KEEP" -ge 0 ]]; then
	idx=0
	for f in "${sorted[@]}"; do
		[[ -n "$f" ]] || continue
		idx=$((idx + 1))
		if [[ "$idx" -gt "$KEEP" ]]; then
			rm -f "$f"
		fi
	done
fi

stable_path="${DIST_DIR}/${STABLE_REL}"
rm -f "$stable_path"
(
	cd "$DIST_DIR"
	ln -sf "$(basename "$NEWEST")" "$STABLE_REL"
)

echo "[OK] ${stable_path} -> $(basename "$NEWEST")"
