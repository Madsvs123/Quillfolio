"""Tests for the loopback preview server."""

import threading
import time
import urllib.error
import urllib.request

import pytest

from quillfolio.preview import LOOPBACK_HOST, make_preview_server

from paths import EXAMPLE


def test_preview_serves_only_the_rendered_resume():
    server = make_preview_server(EXAMPLE, "signal", 0)
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.05},
        daemon=True,
    )
    thread.start()
    try:
        host, port = server.server_address
        assert host == LOOPBACK_HOST == "127.0.0.1"
        assert server.socket.getsockname()[0] == "127.0.0.1"
        deadline = time.time() + 5
        body = ""
        policy = ""
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                    assert response.status == 200
                    body = response.read().decode("utf-8")
                    policy = response.headers.get("Content-Security-Policy", "")
                break
            except urllib.error.URLError:
                time.sleep(0.05)
        else:
            pytest.fail("preview server did not respond")
        assert "theme-signal" in body
        assert "Marlowe Voss" in body
        assert "default-src 'none'" in policy

        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/../../secret", timeout=2)
        assert caught.value.code == 404
        error_body = caught.value.read()
        assert b"Not found" in error_body
        assert b"Marlowe" not in error_body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
