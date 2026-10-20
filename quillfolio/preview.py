"""Serve one rendered resume on the loopback interface."""

from __future__ import annotations

import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from quillfolio.errors import ResumeError
from quillfolio.html_render import normalize_theme, render_html
from quillfolio.resume_io import MAX_RESUME_BYTES, load_resume

LOOPBACK_HOST = "127.0.0.1"
_ALLOWED_PATHS = {"/", "/index.html"}


class _PreviewServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_preview_server(resume_path: Path | str, theme: str, port: int = 8765) -> _PreviewServer:
    """Bind an HTTP server to 127.0.0.1 that renders one local resume file.

    The handler answers only `/` and `/index.html`. Each response is rebuilt
    from that file. Nothing is uploaded, and no other path is served.
    """
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ResumeError("port must be an integer from 0 to 65535")
    resume_file = Path(resume_path).resolve()
    if not resume_file.is_file():
        raise ResumeError(f"file not found: {resume_file}")
    chosen = normalize_theme(theme)

    class PreviewHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._handle(write_body=True)

        def do_HEAD(self) -> None:
            self._handle(write_body=False)

        def _handle(self, write_body: bool) -> None:
            if urlparse(self.path).path not in _ALLOWED_PATHS:
                self._write(404, "text/plain; charset=utf-8", b"Not found\n", write_body)
                return
            try:
                document = render_preview(resume_file, chosen)
            except ResumeError as exc:
                self._write(500, "text/plain; charset=utf-8", f"{exc}\n".encode("utf-8"), write_body)
                return
            except Exception:
                traceback.print_exc()
                self._write(500, "text/plain; charset=utf-8", b"could not render resume\n", write_body)
                return
            self._write(200, "text/html; charset=utf-8", document.encode("utf-8"), write_body)

        def _write(self, status: int, content_type: str, body: bytes, write_body: bool) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; "
                "connect-src 'none'; base-uri 'none'; form-action 'none'",
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if write_body:
                self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"[preview] {self.address_string()} - {fmt % args}", file=sys.stderr)

    try:
        return _PreviewServer((LOOPBACK_HOST, port), PreviewHandler)
    except OSError as exc:
        raise ResumeError(f"could not listen on {LOOPBACK_HOST}:{port}: {exc}") from exc


def render_preview(resume_path: Path, theme: str) -> str:
    if resume_path.stat().st_size > MAX_RESUME_BYTES:
        raise ResumeError(f"resume file is larger than {MAX_RESUME_BYTES} bytes")
    return render_html(load_resume(resume_path), theme)
