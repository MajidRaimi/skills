from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from dataclasses import asdict, dataclass
from pathlib import Path

DASHES = re.compile("[" + chr(0x2013) + chr(0x2014) + "]")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CURRENCY = "SAR|USD|EUR|AED|riyals?|" + "|".join(
    re.escape(symbol) for symbol in ("$", "£", "€", "\ufdfc", "\u20c1", "\u0631.\u0633")
)
MONEY = re.compile(
    rf"(?:(?:{CURRENCY})\s?\d[\d,.]*)|(?:\d[\d,.]*\s?(?:{CURRENCY}))",
    re.IGNORECASE,
)
LEFTOVERS = re.compile(r"<(?:REPO|PRODUCT|DATE|SOURCES|FILE)>|\bTODO\b|[Ll]orem ipsum")
DEFAULT_FILES = ("PRODUCT.md", "DESIGN.md")
DECISIONS = "DECISIONS.md"


@dataclass(frozen=True)
class Problem:
    level: str
    file: str
    line: int
    rule: str
    text: str


def default_targets(root: Path) -> list[Path]:
    docs = [
        path
        for folder in ("product", "build")
        for path in sorted((root / "docs" / folder).rglob("*.md"))
    ]
    return [root / name for name in DEFAULT_FILES if (root / name).is_file()] + docs


def link_target(source: Path, raw: str) -> Path | None:
    if raw.startswith(("http://", "https://", "mailto:", "#", "memory://", "~")):
        return None
    path = urllib.parse.unquote(raw.split("#", 1)[0])
    return (source.parent / path).resolve() if path else None


def check_file(root: Path, path: Path) -> list[Problem]:
    relative = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    problems: list[Problem] = []
    fence = ""
    links_decisions = path.name == DECISIONS
    for number, line in enumerate(lines, start=1):
        marker = FENCE.match(line)
        if marker and not fence:
            fence = marker.group(1)
        elif marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
            fence = ""
        if DASHES.search(line):
            problems.append(Problem("error", relative, number, "dash", line.strip()[:160]))
        if LEFTOVERS.search(line):
            problems.append(Problem("error", relative, number, "leftover", line.strip()[:160]))
        if not fence and MONEY.search(line):
            problems.append(Problem("warn", relative, number, "money", line.strip()[:160]))
        if DECISIONS in line:
            links_decisions = True
        for raw in [] if fence else LINK.findall(INLINE_CODE.sub("", line)):
            target = link_target(path, raw)
            if target is not None and not target.exists():
                problems.append(Problem("error", relative, number, "broken-link", raw))
    if fence:
        problems.append(Problem("error", relative, len(lines), "unclosed-fence", fence))
    if not links_decisions:
        problems.append(
            Problem("warn", relative, 1, "no-decisions-ref", f"never names {DECISIONS}")
        )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(prog="check_docs")
    parser.add_argument("root", type=Path)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    targets = [(root / f).resolve() for f in args.files] or default_targets(root)
    missing = [str(t) for t in targets if not t.is_file()]
    if missing or not targets:
        print(json.dumps({"error": "no such files", "missing": missing}))
        raise SystemExit(2)
    problems = [p for t in targets for p in check_file(root, t)]
    errors = sum(p.level == "error" for p in problems)
    summary = {
        "files": len(targets),
        "lines": sum(len(t.read_text(encoding="utf-8").splitlines()) for t in targets),
        "errors": errors,
        "warnings": len(problems) - errors,
        "problems": [asdict(p) for p in problems],
    }
    sys.stdout.write(json.dumps(summary, ensure_ascii=True, indent=1) + "\n")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
