#!/bin/bash
# 启动交易系统 gunicorn 服务
# 用法: bash start_gunicorn.sh

WORKSPACE="/root/.openclaw/workspace"
PID_FILE="/tmp/gunicorn_trading.pid"

cd "$WORKSPACE"

# 停止旧进程
if [ -f "$PID_FILE" ]; then
    kill $(cat "$PID_FILE") 2>/dev/null
fi

# 激活虚拟环境并启动
source sim_trading/venv/bin/activate

nohup gunicorn \
    -w 1 \
    -b 0.0.0.0:80 \
    --timeout 30 \
    --daemon \
    --pid "$PID_FILE" \
    app:app \
    > /tmp/gunicorn.log 2>&1

echo "Gunicorn started with PID $(cat $PID_FILE)"
