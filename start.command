#!/bin/bash
# ダブルクリックでAIライティングツールを起動する
cd "$(dirname "$0")"
echo "AIライティングツールを起動しています..."
echo "終了するときは、このウィンドウを閉じてください。"
(sleep 3 && open http://localhost:8501) &
.venv/bin/streamlit run app.py
