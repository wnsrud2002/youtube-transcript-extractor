#!/bin/bash
cd "$(dirname "$0")"

# mlx-whisper는 Apple Silicon(M1 이상) GPU 전용
if [ "$(uname -m)" != "arm64" ]; then
  echo "고정밀 모드는 Apple Silicon(M1/M2/M3/M4...) Mac에서만 쓸 수 있습니다."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다."
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "먼저 '실행.command'를 한 번 실행해 기본 설치를 마쳐주세요."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다."
  exit 1
fi

echo "고정밀 모드 설치 중 (약 1.2GB, 수 분 걸립니다)..."
if .venv/bin/pip install -q -r requirements-whisper.txt; then
  echo "설치 완료. 화면에서 '고정밀 모드'를 체크하면 됩니다."
  echo "(첫 사용 시 음성 인식 모델 약 1.6GB를 추가로 내려받습니다)"
else
  echo "설치에 실패했습니다. 인터넷 연결과 저장 공간을 확인하세요."
fi
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다."
