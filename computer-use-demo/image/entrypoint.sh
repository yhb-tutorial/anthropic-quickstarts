#!/bin/bash
set -e

# 启动SSH服务
sudo /usr/sbin/sshd

./start_all.sh
./novnc_startup.sh

python http_server.py > /tmp/server_logs.txt 2>&1 &

STREAMLIT_SERVER_PORT=8501 python -m streamlit run computer_use_demo/streamlit.py > /tmp/streamlit_stdout.log &

# 启动 FastAPI 服务
python -m uvicorn computer_use_demo.loop_rest:app --host 0.0.0.0 --port 8000 --reload > /tmp/fastapi_stdout.log 2>&1 &

echo "✨ Computer Use Demo is ready!"
echo "➡️  Open http://localhost:8080 in your browser to begin"

echo "🔒 SSH server is running on port 22"

echo "🚀 FastAPI service is running on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"

# Keep the container running
tail -f /dev/null
