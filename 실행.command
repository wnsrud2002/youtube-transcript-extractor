#!/bin/bash
# 더블클릭 시 홈 디렉토리에서 실행되므로 스크립트 위치로 이동
cd "$(dirname "$0")"
exec .venv/bin/python app.py
