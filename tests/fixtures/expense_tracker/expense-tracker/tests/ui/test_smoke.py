# Generated from the Contract. Do not edit.
"""UI smoke test: `/` loads, no console errors, no failed requests."""

import os
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

sync_api = pytest.importorskip("playwright.sync_api")

PROJECT_DIR = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server_url() -> Iterator[str]:
    port = _free_port()
    db = Path(tempfile.mkdtemp(prefix="ui-smoke-")) / "ui.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1"]
    proc = subprocess.Popen(
        [*cmd, "--port", str(port)],
        cwd=PROJECT_DIR,
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                if httpx.get(url + "/").status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            pytest.fail("server did not start")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_ui_smoke(server_url):
    console_errors: list[str] = []
    failed_requests: list[str] = []
    with sync_api.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.on("requestfailed", lambda r: failed_requests.append(r.url))
        page.on(
            "response",
            lambda r: failed_requests.append(f"{r.status} {r.url}") if r.status >= 400 else None,
        )
        response = page.goto(server_url + "/")
        page.wait_for_load_state("networkidle")
        browser.close()

    assert response is not None and response.status == 200
    assert console_errors == []
    assert failed_requests == []
