# yt-transcript — 개발 플랜

유튜브 링크 → 영상 대사 텍스트(.txt) 추출 CLI.

## 1. 가능 여부

가능. 두 가지 경로:

| 경로 | 방식 | 속도 | 한계 |
|------|------|------|------|
| A. 자막 추출 (기본) | 유튜브에 올라간 자막(수동/자동생성)을 그대로 가져옴 | 1~2초 | 자막이 꺼진 영상은 불가 |
| B. 음성 인식 (폴백) | 오디오 다운로드 → Whisper로 받아쓰기 | 영상 길이의 수 분의 1 ~ 수 배 | 느림, 모델 다운로드 필요 |

대부분의 영상은 자동생성 자막이 있어 A로 충분. B는 A가 실패할 때만.

## 2. 기술 선택

- 언어: Python 3.13 (이미 설치됨)
- A: `youtube-transcript-api` — 자막 전용 라이브러리, API 키 불필요
- B: `yt-dlp`(오디오 다운로드) + `faster-whisper`(로컬 음성 인식) — ffmpeg은 이미 설치됨
- 새 의존성: 위 3개. B는 선택 설치(`pip install .[whisper]`)로 분리해 A만 쓰면 가볍게 유지.

## 3. 구조

```
yt-transcript/
├── yt_transcript.py   # CLI 전체 (단일 파일)
├── test_yt_transcript.py
└── requirements.txt
```

파일을 쪼개지 않음. 200줄 넘어가면 그때 분리.

## 4. 동작 흐름

```
URL 입력
 → video_id 추출 (watch?v=, youtu.be/, shorts/, embed/ 모두 지원)
 → [A] 자막 목록 조회 → 우선순위: 수동 자막(ko) > 수동(en) > 자동생성(ko) > 자동생성(en) > 아무거나
 → 성공: 텍스트 이어붙여 출력
 → 실패(자막 없음) + --whisper 옵션: [B] 오디오 받아 Whisper로 변환
 → stdout 출력 또는 -o 파일 저장
```

## 5. CLI 사양

```bash
python yt_transcript.py <URL>                 # 텍스트를 stdout으로
python yt_transcript.py <URL> -o out.txt      # 파일 저장
python yt_transcript.py <URL> --lang en       # 언어 우선순위 지정
python yt_transcript.py <URL> --timestamps    # [00:12] 형식 타임스탬프 포함
python yt_transcript.py <URL> --whisper       # 자막 없으면 음성 인식 폴백
```

## 6. 단계별 구현

1. **video_id 파서** — 정규식 하나. 여러 URL 형태 테스트로 고정.
2. **자막 추출(A)** — `youtube-transcript-api`로 언어 우선순위 적용, 텍스트 정리(`[음악]` 같은 태그 제거, 줄바꿈 합치기).
3. **CLI** — `argparse`(표준 라이브러리).
4. **Whisper 폴백(B)** — `yt-dlp`로 m4a만 받아 임시 폴더에 저장 → `faster-whisper` small 모델로 변환 → 임시 파일 삭제.
5. **테스트** — 오프라인 테스트는 URL 파서·텍스트 정리만. 네트워크 테스트는 실제 공개 영상 1개로 수동 확인.

1~3단계가 MVP. 4단계는 필요할 때 추가.

## 7. 예외 처리

| 상황 | 처리 |
|------|------|
| 잘못된 URL | "유효한 유튜브 링크가 아닙니다" 후 종료 코드 1 |
| 자막 없음 | `--whisper` 사용 안내 메시지 |
| 비공개/연령 제한/삭제된 영상 | 원인 메시지 출력 후 종료 |
| 유튜브 IP 차단(요청 과다) | 재시도 안내. 반복 호출 시 간격 두기 |

## 8. 주의사항

- 유튜브 비공식 경로를 쓰므로 유튜브 쪽 변경으로 깨질 수 있음 → 라이브러리 업데이트로 대응.
- 개인 용도로만 사용. 추출한 텍스트를 재배포하면 저작권 문제 가능.

## 9. 나중에 (지금은 안 함)

- 웹 UI, 재생목록 일괄 처리, LLM 요약 연동 — 필요해지면 추가.
