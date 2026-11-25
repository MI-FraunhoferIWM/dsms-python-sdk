#!/usr/bin/env bash
# run_notebooks.sh: execute and validate all tutorial notebooks
#
# Usage:
#   ./scripts/run_notebooks.sh                         # test all notebooks
#   ./scripts/run_notebooks.sh --refresh               # re-execute and save outputs in-place
#   ./scripts/run_notebooks.sh path/to/nb.ipynb        # test a single notebook
#   ./scripts/run_notebooks.sh --refresh path/to/nb.ipynb  # refresh a single notebook
#
# Requirements: activate your virtual environment first.
#   python -m venv .venv && source .venv/bin/activate
#   pip install -e ".[docs,tests]"
#
# Environment: the notebooks connect to a live DSMS instance.
# Set credentials in a .env file or via environment variables before running:
#   DSMS_HOST_URL, DSMS_USERNAME, DSMS_PASSWORD  (or DSMS_TOKEN)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TUTORIALS_DIR="$REPO_ROOT/docs/dsms_sdk/tutorials"
cd "$REPO_ROOT"

# Collect notebooks
if [ $# -ge 1 ] && [ "$1" = "--refresh" ]; then
    MODE="refresh"
    if [ $# -ge 2 ]; then
        NOTEBOOKS=("${@:2}")
    else
        mapfile -t NOTEBOOKS < <(
            find "$TUTORIALS_DIR" -name "*.ipynb" \
                ! -path "*/.ipynb_checkpoints/*" \
                | sort
        )
    fi
elif [ $# -ge 1 ]; then
    NOTEBOOKS=("$@")
    MODE="test"
else
    mapfile -t NOTEBOOKS < <(
        find "$TUTORIALS_DIR" -name "*.ipynb" \
            ! -path "*/.ipynb_checkpoints/*" \
            | sort
    )
    MODE="test"
fi

# Export .env variables so notebook kernels can connect without a local .env file
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$REPO_ROOT/.env"
    set +a
fi

echo "Found ${#NOTEBOOKS[@]} notebook(s)."
echo ""

if [ "$MODE" = "refresh" ]; then
    echo "Mode: refresh (executing and saving outputs in-place)"
    echo ""
    for nb in "${NOTEBOOKS[@]}"; do
        echo "  Refreshing: $nb"
        jupyter nbconvert \
            --to notebook \
            --execute \
            --inplace \
            --ExecutePreprocessor.timeout=300 \
            "$nb"
    done
    echo ""
    echo "Done. Commit the updated notebooks together with any documentation changes."
else
    echo "Mode: test (pytest + nbmake, outputs not saved)"
    echo ""
    pytest --nbmake "${NOTEBOOKS[@]}"
fi
