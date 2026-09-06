#!/usr/bin/env python3
"""Load a bounded handoff and private notes matching the session directory."""
import json
import os
from pathlib import Path
import subprocess
import sys


def git(cwd, *args):
    result = subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else ""


def context(cwd, memory):
    cwd = Path(cwd).resolve()
    root = git(cwd, "rev-parse", "--show-toplevel")
    project = Path(root) if root else cwd
    parts = []
    handoff = cwd / "HANDOFF.md"
    if not handoff.is_file():
        handoff = project / "HANDOFF.md"
    if handoff.is_file():
        data = handoff.read_text()[:16000]
        if data.startswith("# HANDOFF"):
            parts.append("Saved handoff (verify against current state):\n" + "\n".join(data.splitlines()[:120]))
            if root:
                parts.append("Current branch: " + git(project, "branch", "--show-current")
                             + "\nGit status:\n" + git(project, "status", "--short")[:3000]
                             + "\nRecent commits:\n" + git(project, "log", "--oneline", "-5"))
    index = memory / "index.json"
    if index.is_file():
        for entry in json.loads(index.read_text()):
            scope = entry.get("scope")
            if scope and not cwd.is_relative_to(Path(scope).expanduser().resolve()):
                continue
            note = (memory / entry["file"]).resolve()
            if not note.is_relative_to(memory.resolve()):
                continue
            if note.is_file():
                parts.append("Private saved context (historical facts may need rechecking):\n" + note.read_text()[:12000])
    return "\n\n".join(parts)[:24000]


def main():
    if os.environ.get("CODEX_CONSULT_ACTIVE"):
        return
    try:
        event = json.load(sys.stdin)
        memory = Path.home() / ".config/codex-private-memory"
        text = context(event.get("cwd", os.getcwd()), memory)
        if text:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        print("Session context unavailable; inspect handoff/private notes manually.", file=sys.stderr)


if __name__ == "__main__":
    main()
