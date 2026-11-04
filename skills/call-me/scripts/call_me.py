import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("BLAND_API_BASE", "https://api.bland.ai/v1")
ENV_FILE = Path(os.environ.get("CALL_ME_ENV_FILE", Path.home() / ".config" / "call-me" / "env"))
ENDED_STATUSES = {"completed", "failed", "busy", "no-answer", "canceled", "cancelled"}
SUMMARY_PROMPT = (
    "In 1-3 sentences, state exactly what the user decided or answered, including any "
    "conditions or extra instructions. If they gave no clear answer, say so. Add nothing "
    "they did not say."
)
REQUIRED_KEYS = ("BLAND_API_KEY", "OWNER_PHONE")
OPTIONAL_KEYS = (
    "BLAND_ENCRYPTED_KEY",
    "CALL_ME_VOICE",
    "CALL_ME_FROM",
    "OWNER_NAME",
    "CALL_ME_FIRST_SENTENCE",
)


def load_settings() -> dict[str, str]:
    settings: dict[str, str] = {}
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip():
                settings[key.strip()] = value.strip()
    for key in (*REQUIRED_KEYS, *OPTIONAL_KEYS):
        if os.environ.get(key):
            settings[key] = os.environ[key]
    missing = [key for key in REQUIRED_KEYS if not settings.get(key)]
    if missing:
        raise SystemExit(f"missing {', '.join(missing)} in {ENV_FILE} or the environment")
    return settings


def request(
    method: str, path: str, settings: dict[str, str], body: dict[str, object] | None = None
) -> dict[str, object]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"authorization": settings["BLAND_API_KEY"], "content-type": "application/json"}
    if settings.get("BLAND_ENCRYPTED_KEY"):
        headers["encrypted_key"] = settings["BLAND_ENCRYPTED_KEY"]
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise SystemExit(f"Bland returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Bland is unreachable: {error.reason}") from error
    return payload if isinstance(payload, dict) else {}


def first_sentence(settings: dict[str, str]) -> str:
    if settings.get("CALL_ME_FIRST_SENTENCE"):
        return settings["CALL_ME_FIRST_SENTENCE"]
    name = settings.get("OWNER_NAME", "there")
    return f"Hey {name}, it's your agent's assistant. Got a sec for a quick question?"


def build_task(question: str, options: str, background: str, settings: dict[str, str]) -> str:
    owner = settings.get("OWNER_NAME", "the owner")
    lines = [
        f"You are an assistant calling {owner} on behalf of their AI coding agent, which needs "
        "one decision from them to keep working.",
        f"The question: {question}",
    ]
    if options:
        lines.append(f"The options: {options}")
    if background:
        lines.append(f"Background, share only if they ask: {background}")
    lines.append(
        "Rules: talk fast and tight, short sentences, no small talk. Ask the question and read "
        "the options. If the answer is vague, ask one follow-up. Repeat the decision back in "
        "one sentence and confirm it. If they can't talk or say 'you decide', say the agent "
        "will use its best judgment and end the call. Never decide for them, promise anything, "
        "or discuss other topics. After they confirm, ask 'Anything else before I let you go?' "
        "and only hang up once they say that's all. If they say 'wait' or 'hold on', stop and "
        "listen."
    )
    return "\n".join(lines)


def place_call(settings: dict[str, str], args: argparse.Namespace) -> str:
    body: dict[str, object] = {
        "phone_number": settings["OWNER_PHONE"],
        "task": build_task(args.question, args.options, args.background, settings),
        "first_sentence": first_sentence(settings),
        "wait_for_greeting": True,
        "max_duration": args.max_minutes,
        "summary_prompt": SUMMARY_PROMPT,
        "interruptibility": 3,
        "voice": settings.get("CALL_ME_VOICE", "ryan"),
        "voicemail": {
            "action": "leave_message",
            "message": f"{args.voicemail or args.question} Check your agent when you can.",
        },
    }
    if settings.get("CALL_ME_FROM"):
        body["from"] = settings["CALL_ME_FROM"]
    response = request("POST", "/calls", settings, body)
    call_id = response.get("call_id")
    if response.get("status") != "success" or not isinstance(call_id, str):
        raise SystemExit(f"call failed: {json.dumps(response)[:500]}")
    return call_id


def has_ended(call: dict[str, object]) -> bool:
    status = str(call.get("status") or "").lower()
    queue = str(call.get("queue_status") or "").lower()
    return bool(call.get("completed")) or status in ENDED_STATUSES or queue == "complete" or "error" in queue


def user_spoke(call: dict[str, object]) -> bool:
    transcripts = call.get("transcripts")
    if not isinstance(transcripts, list):
        return False
    return any(isinstance(line, dict) and line.get("user") == "user" and line.get("text") for line in transcripts)


def classify(call: dict[str, object]) -> str:
    answered_by = str(call.get("answered_by") or "").lower()
    if not has_ended(call):
        return "in_progress"
    if "voicemail" in answered_by:
        return "voicemail"
    if user_spoke(call):
        return "answered"
    return "no_answer"


def wait_for(settings: dict[str, str], call_id: str, timeout: int) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    call = request("GET", f"/calls/{call_id}", settings)
    while not has_ended(call) and time.monotonic() < deadline:
        print(f"waiting: status={call.get('status')} queue={call.get('queue_status')}", file=sys.stderr)
        time.sleep(5)
        call = request("GET", f"/calls/{call_id}", settings)
    summary_deadline = min(deadline, time.monotonic() + 60)
    while has_ended(call) and not call.get("summary") and time.monotonic() < summary_deadline:
        time.sleep(5)
        call = request("GET", f"/calls/{call_id}", settings)
    return call


def report(call_id: str, call: dict[str, object]) -> None:
    result = {
        "call_id": call_id,
        "outcome": classify(call),
        "status": call.get("status"),
        "answered_by": call.get("answered_by"),
        "minutes": call.get("call_length"),
        "summary": call.get("summary"),
        "transcript": call.get("concatenated_transcript"),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(prog="call_me")
    parser.add_argument("--question")
    parser.add_argument("--options", default="")
    parser.add_argument("--background", default="")
    parser.add_argument("--voicemail", default="")
    parser.add_argument("--max-minutes", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=540)
    parser.add_argument("--resume", help="keep polling an existing call_id instead of calling again")
    args = parser.parse_args()
    settings = load_settings()
    if args.resume:
        call_id = args.resume
    elif args.question:
        call_id = place_call(settings, args)
        print(f"calling, call_id={call_id}", file=sys.stderr)
    else:
        parser.error("--question or --resume is required")
    report(call_id, wait_for(settings, call_id, args.timeout))


if __name__ == "__main__":
    main()
