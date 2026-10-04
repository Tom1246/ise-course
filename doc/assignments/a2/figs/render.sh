#!/usr/bin/env bash
# A2 —— 重渲染 figs/ 下全部 Graphviz 图（.dot -> 同名 .png）
# 用法: bash doc/assignments/a2/figs/render.sh
set -euo pipefail
cd "$(dirname "$0")"
for f in *.dot; do
  dot -Tpng "$f" -o "${f%.dot}.png"
  echo "rendered ${f%.dot}.png"
done
