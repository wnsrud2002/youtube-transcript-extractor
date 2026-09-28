#!/bin/bash
# 더블클릭 시 홈 디렉토리에서 실행되므로 스크립트 위치로 이동
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
    echo "Python 3.9 이상이 필요합니다. README의 '1. Python 준비'를 참고하세요."
    read -n 1 -s -r -p "아무 키나 누르면 닫힙니다."
    exit 1
  fi
  echo "처음 실행: 필요한 프로그램을 설치합니다 (1분 정도)..."
  # 설치 도중 실패하면 반쯤 만들어진 .venv 때문에 다음 실행이 건너뛰지 않게 지움
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || {
    rm -rf .venv
    echo "설치에 실패했습니다. 인터넷 연결을 확인하고 다시 실행하세요."
    read -n 1 -s -r -p "아무 키나 누르면 닫힙니다."
    exit 1
  }
fi

exec .venv/bin/python app.py
