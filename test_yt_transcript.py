from types import SimpleNamespace as NS

from yt_transcript import clean, pick, render, stamp, video_id

VID = "dQw4w9WgXcQ"


def test_video_id():
    for url in [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://www.youtube.com/watch?list=PL1&v={VID}&t=30s",
        f"https://youtu.be/{VID}?si=abc",
        f"https://youtube.com/shorts/{VID}",
        f"https://www.youtube.com/embed/{VID}",
        f"https://m.youtube.com/live/{VID}",
        VID,
    ]:
        assert video_id(url) == VID, url
    assert video_id("https://example.com") is None
    assert video_id("abc") is None


def test_pick_priority():
    T = lambda lang, gen: NS(language_code=lang, is_generated=gen)
    ko_auto, en_manual, ja = T("ko", True), T("en", False), T("ja", False)
    assert pick([ko_auto, en_manual], ["ko", "en"]) is en_manual  # 수동이 자동생성보다 우선
    assert pick([ko_auto, T("en", True)], ["ko", "en"]) is ko_auto
    assert pick([ja], ["ko", "en"]) is ja
    assert pick([], ["ko"]) is None


def test_clean_and_render():
    assert clean("[음악]  안녕\n하세요 [Music]") == "안녕 하세요"
    sn = [NS(text="[박수]", start=0), NS(text="hello", start=5.2), NS(text="world", start=3725)]
    assert render(sn) == "hello world"
    assert render(sn, timestamps=True) == "[00:05] hello\n[1:02:05] world"
    assert stamp(59.9) == "00:59"


def test_markdown():
    from yt_transcript import md_body, md_escape, md_header

    assert md_escape("# 1*2 [a]_b <i>") == r"\# 1\*2 [a]_b \<i\>"
    assert md_escape("a #tag") == "a #tag"  # 줄 중간 #은 그대로
    sn = [NS(text="[음악]", start=0), NS(text="#첫 줄", start=5.2), NS(text="둘", start=30), NS(text="셋", start=61)]
    assert md_body(sn, VID) == "\\#첫 줄 둘\n\n셋"  # 1분 단위 문단, 효과음 태그 제거
    assert md_body(sn, VID, timestamps=True).splitlines()[0] == f"- [00:05](https://youtu.be/{VID}?t=5) \\#첫 줄"
    h = md_header(VID, {"title": "제목 *강조*", "author": "채널"}, "ko 자막")
    assert h.startswith("# 제목 \\*강조\\*\n") and "- 채널: 채널" in h and h.endswith("---\n\n")
    assert md_header(VID, {}, "ko 자막").startswith(f"# YouTube 영상 {VID}\n")  # 제목 조회 실패 시
    assert "채널" not in md_header(VID, {}, "ko 자막")
