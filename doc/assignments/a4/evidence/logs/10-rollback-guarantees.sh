#!/bin/bash
# A4 rollback evidence — the machine-checked guarantees behind rollback.md
# Run from the A4 work tree. Read-only except for removing the tsc cache.
cd "<A4>/work/UCAS-course-planner" || exit 1
rm -f tsconfig.tsbuildinfo

echo "切片 commit: $(git rev-parse --short a4-slice)"
echo "改动文件数: $(git diff upstream/main --name-only | wc -l | tr -d ' ')"
echo "新增行数:  $(git diff upstream/main --numstat | awk '{s+=$1} END {print s}')"
echo "删除行数:  $(git diff upstream/main --numstat | awk '{s+=$2} END {print s}')   <-- 0 = 纯加法"
echo "碰到持久化契约的行数: $(git diff upstream/main -- app/page.tsx | grep -cE 'PLAN_STORAGE_KEY|storageVersion|setItem|getItem|removeItem')   <-- 0 = 回滚不会碰用户数据"
echo "新增依赖的文件数: $(git diff upstream/main --name-only | grep -cE 'package.json|package-lock.json')   <-- 0 = 不引新依赖"
echo
echo "改动文件清单:"
git diff upstream/main --name-only | sed 's/^/  /'
