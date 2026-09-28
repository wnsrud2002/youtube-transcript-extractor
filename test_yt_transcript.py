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
