#!/bin/bash
# 双击运行：在浏览器里打开本地选课参考系统（纯本地文件，不联网、不起服务）
cd "$(dirname "$0")" || exit 1
if [ ! -f "选课参考系统.html" ]; then
  echo "没有找到 选课参考系统.html，正在重新生成…"
  python3 ../src/build_web_prototype.py || { echo "生成失败，请把上面的报错发给助手"; read -r -p "按回车关闭"; exit 1; }
fi
open "选课参考系统.html"
