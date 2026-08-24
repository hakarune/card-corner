"""Tests for ui.update_check. All network access is mocked -- these must
never make a real HTTP call.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.error

import pytest

from ui import update_check
from ui.update_check import UpdateChecker, UpdateCheckResult, _parse_version, check_for_update_now
from version import __version__


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_parse_version_basic():
    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_with_v_prefix():
    assert _parse_version("v1.2.3") == (1, 2, 3)


def test_parse_version_pads_missing_components():
    assert _parse_version("2") == (2, 0, 0)
    assert _parse_version("2.5") == (2, 5, 0)


def test_parse_version_drops_non_numeric_suffix():
    assert _parse_version("1.2.3-beta") == (1, 2, 3)


def test_check_for_update_now_success(monkeypatch):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse(
            {"tag_name": "v99.0.0", "html_url": "https://example.invalid/release"}
        ),
    )
    result = check_for_update_now()
    assert result.ok
    assert result.latest_version == "v99.0.0"
    assert result.release_url == "https://example.invalid/release"
    assert result.update_available


def test_check_for_update_now_current_version_is_not_an_update(monkeypatch):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse({"tag_name": f"v{__version__}"}),
    )
    result = check_for_update_now()
    assert result.ok
    assert not result.update_available


def test_check_for_update_now_older_remote_is_not_an_update(monkeypatch):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse({"tag_name": "v0.0.1"}),
    )
    result = check_for_update_now()
    assert result.ok
    assert not result.update_available


@pytest.mark.parametrize(
    "exc",
    [
        urllib.error.URLError("no network"),
        socket.timeout("timed out"),
        TimeoutError("timed out"),
        OSError("connection refused"),
        json.JSONDecodeError("bad json", "doc", 0),
        ValueError("unexpected"),
    ],
)
def test_check_for_update_now_never_raises_on_network_failures(monkeypatch, exc):
    def raise_it(req, timeout=None):
        raise exc

    monkeypatch.setattr(update_check.urllib.request, "urlopen", raise_it)
    result = check_for_update_now()  # must not raise
    assert not result.ok
    assert result.error
    assert not result.update_available


def test_check_for_update_now_missing_tag_name_is_handled_gracefully(monkeypatch):
    monkeypatch.setattr(
        update_check.urllib.request, "urlopen", lambda req, timeout=None: FakeResponse({})
    )
    result = check_for_update_now()
    assert not result.ok
    assert not result.update_available


def test_update_result_update_available_false_when_not_ok():
    result = UpdateCheckResult(ok=False, latest_version="v99.0.0")
    assert not result.update_available


def test_update_checker_runs_in_background_and_reports_result(monkeypatch):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse({"tag_name": "v99.0.0"}),
    )
    checker = UpdateChecker()
    assert checker.result is None
    assert not checker.checking
    checker.start()

    deadline = time.monotonic() + 2.0
    while checker.checking and time.monotonic() < deadline:
        time.sleep(0.01)

    assert not checker.checking
    assert checker.result is not None
    assert checker.result.update_available


def test_update_checker_start_is_idempotent_while_already_checking(monkeypatch):
    started = []

    def slow_urlopen(req, timeout=None):
        started.append(1)
        time.sleep(0.2)
        return FakeResponse({"tag_name": "v99.0.0"})

    monkeypatch.setattr(update_check.urllib.request, "urlopen", slow_urlopen)
    checker = UpdateChecker()
    checker.start()
    checker.start()  # should not spawn a second concurrent check
    time.sleep(0.3)
    assert len(started) == 1
