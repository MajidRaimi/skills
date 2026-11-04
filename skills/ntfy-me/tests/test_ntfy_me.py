from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ntfy_me import (
    NtfyMeError,
    Origin,
    Settings,
    build_payload,
    encode_header,
    file_headers,
    load_settings,
    parse_action,
    resolve_origin,
)

SETTINGS = Settings("https://ntfy.example", "my-alerts", "tk_secret")


def test_title_prefers_ntfy_title_env() -> None:
    origin = resolve_origin({"NTFY_TITLE": "CI bot"}, Path("/x"))
    assert origin.title == "CI bot"


def test_title_falls_back_to_folder_name() -> None:
    origin = resolve_origin({}, Path("/home/user/repo"))
    assert origin.title == "repo"


def test_click_url_comes_from_env() -> None:
    origin = resolve_origin({"NTFY_CLICK_URL": "https://app.example/s/1"}, Path("/x"))
    assert origin.click == "https://app.example/s/1"


def test_payload_maps_kind_to_tag_and_priority() -> None:
    payload = build_payload(SETTINGS, Origin("t", "https://c"), " done ", "done", tags=["tada"])
    assert payload["tags"] == ["white_check_mark", "tada"]
    assert payload["priority"] == 3
    assert payload["message"] == "done"
    assert payload["click"] == "https://c"
    assert payload["markdown"] is True
    assert build_payload(SETTINGS, Origin("t"), "x", "urgent")["priority"] == 5
    assert "click" not in build_payload(SETTINGS, Origin("t"), "x", "info")


def test_payload_rejects_bad_input() -> None:
    with pytest.raises(NtfyMeError):
        build_payload(SETTINGS, Origin("t"), "x", "loud")
    with pytest.raises(NtfyMeError):
        build_payload(SETTINGS, Origin("t"), "   ", "info")
    with pytest.raises(NtfyMeError):
        build_payload(SETTINGS, Origin("t"), "x", "info", actions=["a=https://a"] * 4)


def test_actions_parse_and_validate() -> None:
    assert parse_action("Open PR=https://gitlab/x?a=b") == {
        "action": "view",
        "label": "Open PR",
        "url": "https://gitlab/x?a=b",
        "clear": False,
    }
    with pytest.raises(NtfyMeError):
        parse_action("no url here")
    with pytest.raises(NtfyMeError):
        parse_action("Bad=ftp://x")


def test_file_headers_encode_unicode_and_keep_token_out_of_payload() -> None:
    payload = build_payload(
        SETTINGS, Origin("📚 MyProj · x"), "line1\nline2", "blocked", actions=["Open=https://o"]
    )
    headers = file_headers(SETTINGS, payload, Path("/tmp/shot.png"))
    assert headers["Title"].startswith("=?UTF-8?B?")
    assert headers["Message"].startswith("=?UTF-8?B?")
    assert headers["Filename"] == "shot.png"
    assert headers["Priority"] == "4"
    assert headers["Actions"] == "view, Open, https://o"
    assert encode_header("plain") == "plain"
    assert "tk_secret" not in str(payload)


def test_settings_read_env_file_and_overrides(tmp_path: Path) -> None:
    config = tmp_path / "env"
    config.write_text(
        "NTFY_HOST=https://n.example/\nNTFY_TOPIC=my-alerts\nNTFY_TOKEN=tk_a\n",
        encoding="utf-8",
    )
    assert load_settings(config, {}) == Settings("https://n.example", "my-alerts", "tk_a")
    assert load_settings(config, {"NTFY_TOPIC": "other"}).topic == "other"
    with pytest.raises(NtfyMeError):
        load_settings(tmp_path / "missing", {})
