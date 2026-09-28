"""브라우저 UI 서버. 실행: python app.py"""
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from yt_transcript import ExtractError, extract

PAGE = Path(__file__).with_name("index.html")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/extract":
            return self._send(404, b"not found", "text/plain")
        length = int(self.headers.get("Content-Length") or 0)
        if length > 10_000:
            return self._json(413, {"error": "요청이 너무 큽니다."})
        try:
            req = json.loads(self.rfile.read(length))
            langs = [l.strip() for l in str(req.get("lang", "ko,en")).split(",") if l.strip()]
            text, source = extract(str(req.get("url", "")), langs or ["ko", "en"],
                                   bool(req.get("timestamps")), bool(req.get("whisper")))
        except ExtractError as e:
            return self._json(400, {"error": str(e)})
        except (ValueError, AttributeError):
            return self._json(400, {"error": "잘못된 요청입니다."})
        except Exception as e:  # 네트워크 끊김 등 예상 못 한 오류도 화면에 보여줌
            return self._json(500, {"error": f"알 수 없는 오류: {type(e).__name__}"})
        self._json(200, {"text": text, "source": source})

    def log_message(self, fmt, *args):
        pass  # 요청마다 찍히는 로그가 터미널을 덮지 않게


def main(port=8765):
    # 외부에서 접속 못 하게 127.0.0.1에만 바인딩
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:  # 포트 사용 중이면 빈 포트 아무거나
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"실행 중: {url}  (종료: 이 창 닫기 또는 Ctrl+C)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
