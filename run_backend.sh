#!/bin/bash
# 自动在 conda 虚拟环境 aircomp 中启动后端
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"
conda run -n aircomp --no-capture-output uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
