#!/bin/sh
set -e

# 自动安装依赖
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
  echo "检测到依赖变更，正在安装npm包..."
  npm install
fi

exec "$@"
