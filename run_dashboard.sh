#!/bin/bash
# ダッシュボード起動スクリプト

cd "$(dirname "$0")"
echo "Starting CHRO-SIE Dashboard..."
echo "Open your browser to: http://localhost:8501"
echo ""

streamlit run dashboard.py
