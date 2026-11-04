from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

CONFIG = Path.home() / ".config" / "ntfy-me" / "env"
SEND_TIMEOUT_SECONDS = 30
MAX_ACTIONS = 3
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
USER_AGENT = "ntfy-me/1.0"

Json = dict[str, object]


class NtfyMeError(Exception):
    pass


@dataclass(frozen=True)
class Kind:
    tag: str
    priority: int


KINDS: Mapping[str, Kind] = {
    "done": Kind("white_check_mark", 3),
    "info": Kind("speech_balloon", 2),
    "blocked": Kind("warning", 4),
    "error": Kind("x", 4),
    "urgent": Kind("rotating_light", 5),
}


@dataclass(frozen=True)
class Origin:
    title: str
    click: str = ""


@dataclass(frozen=True)
class Settings:
    url: str
    topic: str
    token: str


def load_settings(path: Path = CONFIG, environ: Mapping[str, str] = os.environ) -> Settings:
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and not key.strip().startswith("#"):
                values[key.strip()] = value.strip().strip("'\"")
    host = environ.get("NTFY_HOST", values.get("NTFY_HOST", "")).rstrip("/")
    topic = environ.get("NTFY_TOPIC", values.get("NTFY_TOPIC", ""))
    token = environ.get("NTFY_TOKEN", values.get("NTFY_TOKEN", ""))
    if not host:
        raise NtfyMeError(f"missing NTFY_HOST in environment or {path}")
    if not topic:
        raise NtfyMeError(f"missing NTFY_TOPIC in environment or {path}")
    return Settings(host, topic, token)


def text(value: object) -> str:
    return value if isinstance(value, str) else ""


def mapping(value: object) -> Json:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}


def resolve_origin(environ: Mapping[str, str], cwd: Path) -> Origin:
    title = environ.get("NTFY_TITLE", "")
    if not title:
        title = cwd.name or environ.get("NTFY_TITLE_FALLBACK", "") or "notification"
    click = environ.get("NTFY_CLICK_URL", "")
    return Origin(title, click)


def parse_action(raw: str) -> Json:
    label, separator, url = raw.partition("=")
    if not separator or not label.strip() or not url.strip().startswith(("http://", "https://")):
        raise NtfyMeError(f"action {raw!r} must look like 'Label=https://...'")
    return {"action": "view", "label": label.strip(), "url": url.strip(), "clear": False}


def build_payload(
    settings: Settings,
    origin: Origin,
    message: str,
    kind: str,
    actions: Sequence[str] = (),
    tags: Sequence[str] = (),
    click: str = "",
    attach_url: str = "",
    markdown: bool = True,
    priority: int | None = None,
) -> Json:
    if kind not in KINDS:
        raise NtfyMeError(f"unknown kind {kind!r}; use one of {', '.join(KINDS)}")
    if len(actions) > MAX_ACTIONS:
        raise NtfyMeError(f"at most {MAX_ACTIONS} actions")
    if not message.strip():
        raise NtfyMeError("the message is empty")
    payload: Json = {
        "topic": settings.topic,
        "title": origin.title,
        "message": message.strip(),
        "tags": [KINDS[kind].tag, *[tag.strip() for tag in tags if tag.strip()]],
        "priority": priority or KINDS[kind].priority,
        "markdown": markdown,
    }
    if click or origin.click:
        payload["click"] = click or origin.click
    if actions:
        payload["actions"] = [parse_action(action) for action in actions]
    if attach_url:
        payload["attach"] = attach_url
    return payload


def encode_header(value: str) -> str:
    if value.isascii() and "\n" not in value:
        return value
    return f"=?UTF-8?B?{base64.b64encode(value.encode()).decode()}?="


def action_header(actions: object) -> str:
    entries = actions if isinstance(actions, list) else []
    return "; ".join(
        f"view, {text(entry.get('label'))}, {text(entry.get('url'))}"
        for entry in entries
        if isinstance(entry, dict)
    )


def file_headers(settings: Settings, payload: Json, attachment: Path) -> dict[str, str]:
    tags = payload.get("tags")
    headers = {
        "Authorization": f"Bearer {settings.token}",
        "User-Agent": USER_AGENT,
        "Filename": attachment.name,
        "Title": encode_header(text(payload.get("title"))),
        "Message": encode_header(text(payload.get("message"))),
        "Tags": ",".join(tag for tag in tags if isinstance(tag, str))
        if isinstance(tags, list)
        else "",
        "Priority": str(payload.get("priority")),
        "Markdown": "yes" if payload.get("markdown") else "no",
    }
    if payload.get("click"):
        headers["Click"] = text(payload.get("click"))
    if payload.get("actions"):
        headers["Actions"] = encode_header(action_header(payload.get("actions")))
    return headers


def send(request: urllib.request.Request) -> Json:
    try:
        with urllib.request.urlopen(request, timeout=SEND_TIMEOUT_SECONDS) as response:
            return mapping(json.loads(response.read() or b"{}"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:300]
        raise NtfyMeError(f"ntfy returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise NtfyMeError(f"ntfy unreachable: {error.reason}") from error


def publish(settings: Settings, payload: Json, attachment: Path | None) -> Json:
    if attachment is None:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if settings.token:
            headers["Authorization"] = f"Bearer {settings.token}"
        request = urllib.request.Request(
            settings.url,
            data=json.dumps(payload).encode(),
            method="POST",
            headers=headers,
        )
        return send(request)
    request = urllib.request.Request(
        f"{settings.url}/{settings.topic}",
        data=attachment.read_bytes(),
        method="PUT",
        headers=file_headers(settings, payload, attachment),
    )
    return send(request)


def checked_attachment(raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_file():
        raise NtfyMeError(f"attachment {path} does not exist")
    if path.stat().st_size > MAX_ATTACHMENT_BYTES:
        raise NtfyMeError(f"attachment {path} is over 10 MB")
    return path


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ntfy-me", description="Push a notification via ntfy")
    parser.add_argument("message", nargs="?", help="message body; read from stdin when omitted")
    parser.add_argument("--kind", default="info", choices=list(KINDS))
    parser.add_argument("--title", help="override the automatic title")
    parser.add_argument("--action", action="append", default=[], help="'Label=https://...'")
    attach = parser.add_mutually_exclusive_group()
    attach.add_argument("--attach", help="local file to attach (10 MB max)")
    attach.add_argument("--attach-url", default="", help="URL of a file to attach")
    parser.add_argument("--click", default="", help="URL opened when the notification is tapped")
    parser.add_argument("--tags", default="", help="extra comma-separated ntfy tags or emoji names")
    parser.add_argument("--priority", type=int, choices=range(1, 6), help="override 1-5")
    parser.add_argument("--plain", action="store_true", help="send the body as plain text")
    parser.add_argument("--dry-run", action="store_true", help="print the payload, send nothing")
    return parser.parse_args(argv)


def run(argv: Sequence[str]) -> Json:
    args = parse_args(argv)
    message = args.message if args.message is not None else sys.stdin.read()
    settings = load_settings()
    origin = (
        Origin(args.title, os.environ.get("NTFY_CLICK_URL", ""))
        if args.title
        else resolve_origin(os.environ, Path.cwd())
    )
    payload = build_payload(
        settings,
        origin,
        message,
        args.kind,
        actions=args.action,
        tags=args.tags.split(",") if args.tags else (),
        click=args.click,
        attach_url=args.attach_url,
        markdown=not args.plain,
        priority=args.priority,
    )
    attachment = checked_attachment(args.attach)
    if args.dry_run:
        return {"dry_run": True, "payload": payload, "attachment": str(attachment or "")}
    result = publish(settings, payload, attachment)
    return {"sent": True, "id": result.get("id"), "title": origin.title, "kind": args.kind}


def main() -> None:
    try:
        print(json.dumps(run(sys.argv[1:]), ensure_ascii=False))
    except NtfyMeError as error:
        print(f"ntfy-me: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
