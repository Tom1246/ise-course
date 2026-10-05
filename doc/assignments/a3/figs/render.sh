#!/bin/bash
# A3 — regenerate the diagrams from their Graphviz sources.
# Requires Graphviz (`dot`). Run from this directory: bash render.sh
set -e
cd "$(dirname "$0")"
for f in *.dot; do
  dot -Tpng "$f" -o "${f%.dot}.png"
  echo "rendered ${f%.dot}.png ($(stat -f %z "${f%.dot}.png") bytes)"
done
