"""유튜브 링크 → 대사 텍스트."""
import argparse
import re
import sys

ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")
# 자동생성 자막에 섞이는 [음악], [Music], [박수] 같은 효과음 태그
TAG_RE = re.compile(r"\[[^\]]*\]")


def video_id(url: str) -> str | None:
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    m = ID_RE.search(url)
    return m.group(1) if m else None


def pick(transcripts, langs):
    """수동 자막을 자동생성보다 우선, 그 안에서 langs 순서대로. 없으면 아무거나."""
    transcripts = list(transcripts)
    for generated in (False, True):
        for lang in langs:
            for t in transcripts:
                if t.is_generated == generated and t.language_code == lang:
                    return t
    return transcripts[0] if transcripts else None


def clean(text: str) -> str:
    return " ".join(TAG_RE.sub(" ", text).split())


def stamp(sec: float) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"


def render(snippets, timestamps=False) -> str:
    lines = []
    for sn in snippets:
        text = clean(sn.text)
        if text:
            lines.append(f"[{stamp(sn.start)}] {text}" if timestamps else text)
    return "\n".join(lines) if timestamps else " ".join(lines)


class ExtractError(Exception):
    """사용자에게 그대로 보여줄 한국어 메시지를 담는 오류."""


WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


def transcribe(vid: str, lang: str, timestamps=False) -> str:
    """오디오를 받아 Whisper로 직접 받아쓰기. 자동 자막보다 정확하고 문장부호가 붙음."""
    import tempfile
    import mlx_whisper
    import yt_dlp
    from types import SimpleNamespace

    with tempfile.TemporaryDirectory() as tmp:
        opts = {"format": "bestaudio[ext=m4a]/bestaudio", "outtmpl": f"{tmp}/%(id)s.%(ext)s",
                "quiet": True, "no_warnings": True, "noprogress": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                audio = ydl.prepare_filename(ydl.extract_info(f"https://www.youtube.com/watch?v={vid}"))
        except yt_dlp.utils.DownloadError as e:
            raise ExtractError(f"오디오를 받지 못했습니다: {str(e).removeprefix('ERROR: ')[:200]}")
        result = mlx_whisper.transcribe(
            audio, path_or_hf_repo=WHISPER_MODEL, language=lang,
            # 이전 문장을 조건으로 쓰면 같은 문장을 무한 반복하는 환각이 생겨서 끔
            condition_on_previous_text=False,
            # 문장부호가 있는 예시를 주면 Whisper가 출력에도 문장부호를 붙임
            initial_prompt="안녕하세요. 오늘 수업을 시작하겠습니다." if lang == "ko" else None,
        )
    segs = [SimpleNamespace(text=s["text"], start=s["start"]) for s in result["segments"]]
    return render(segs, timestamps)


def extract(url: str, langs=("ko", "en"), timestamps=False, whisper=False):
    """(텍스트, 출처 설명) 반환. 실패 시 ExtractError."""
    vid = video_id(url.strip())
    if not vid:
        raise ExtractError("유효한 유튜브 링크가 아닙니다.")
    if whisper:
        return transcribe(vid, langs[0], timestamps), f"Whisper 받아쓰기 ({langs[0]})"

    # 파서 테스트가 네트워크 라이브러리 없이 돌도록 여기서 import
    from youtube_transcript_api import (
        YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable,
        AgeRestricted, IpBlocked, RequestBlocked, CouldNotRetrieveTranscript,
    )

    try:
        t = pick(YouTubeTranscriptApi().list(vid), list(langs))
        if t is None:
            raise ExtractError("이 영상에는 자막이 없습니다.")
        return render(t.fetch(), timestamps), f"{t.language_code}{' 자동생성' if t.is_generated else ''} 자막"
    except TranscriptsDisabled:
        raise ExtractError("이 영상은 자막이 꺼져 있습니다.")
    except VideoUnavailable:
        raise ExtractError("영상을 찾을 수 없습니다 (비공개/삭제).")
    except AgeRestricted:
        raise ExtractError("연령 제한 영상이라 자막을 가져올 수 없습니다.")
    except (IpBlocked, RequestBlocked):
        raise ExtractError("유튜브가 요청을 차단했습니다. 잠시 후 다시 시도하세요.")
    except CouldNotRetrieveTranscript as e:
        raise ExtractError(f"자막을 가져오지 못했습니다: {type(e).__name__}")


def main(argv=None):
    p = argparse.ArgumentParser(description="유튜브 영상 자막을 텍스트로 추출")
    p.add_argument("url")
    p.add_argument("-o", "--output", help="저장할 파일 경로 (생략 시 화면 출력)")
    p.add_argument("--lang", default="ko,en", help="언어 우선순위, 쉼표 구분 (기본 ko,en)")
    p.add_argument("--timestamps", action="store_true", help="줄마다 [mm:ss] 표시")
    p.add_argument("--whisper", action="store_true", help="자막 대신 음성을 직접 받아쓰기 (정확하지만 느림)")
    args = p.parse_args(argv)

    try:
        text, source = extract(args.url, args.lang.split(","), args.timestamps, args.whisper)
    except ExtractError as e:
        sys.exit(str(e))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"저장: {args.output} ({source})", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
