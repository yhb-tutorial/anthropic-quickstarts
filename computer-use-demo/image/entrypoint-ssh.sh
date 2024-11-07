#!/bin/bash
set -e

# 启动SSH服务（需要sudo权限）
# sudo service ssh start
# 启动SSH服务
sudo /usr/sbin/sshd

# ./start_all.sh
# ./novnc_startup.sh

# python http_server.py > /tmp/server_logs.txt 2>&1 &

# STREAMLIT_SERVER_PORT=8501 python -m streamlit run computer_use_demo/streamlit.py > /tmp/streamlit_stdout.log &

echo "✨ Computer Use Demo is ready!"
echo "➡️  Open http://localhost:8080 in your browser to begin"
echo "🔒 SSH is enabled - connect using:"
echo "   ssh computeruse@<host> with password: computeruse"

# Keep the container running
tail -f /dev/null