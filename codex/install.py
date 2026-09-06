#!/usr/bin/env python3
"""Install portable Codex settings and linked skills, with backups."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
PONYTAIL_REF = "2ed6c52c9d7e5e56942508591085fd45dea277d3"


def merge_setting(text, section, key, value):
    header = "[" + section + "]" if section else None
    start = 0
    if header:
        match = re.search(r"(?m)^" + re.escape(header) + r"\s*$", text)
        if not match:
            return text.rstrip() + "\n\n" + header + "\n" + key + " = " + json.dumps(value) + "\n"
        start = match.end()
    end_match = re.search(r"(?m)^\[", text[start:])
    end = start + end_match.start() if end_match else len(text)
    body = text[start:end]
    pattern = r"(?m)^" + re.escape(key) + r"\s*=\s*(?:\[[\s\S]*?\]|[^\n]*)"
    line = key + " = " + json.dumps(value)
    if re.search(pattern, body):
        body = re.sub(pattern, lambda _: line, body, count=1)
    else:
        body = body.rstrip() + "\n" + line + "\n\n"
    return text[:start] + body + text[end:]


def install(home, ponytail=False, migrate_memory=False):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = home / ".config/codex-backups" / stamp
    changed = []

    def save(path):
        if path.exists() or path.is_symlink():
            dest = backup / path.relative_to(home)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink():
                dest.symlink_to(os.readlink(path))
            elif path.is_dir():
                shutil.copytree(path, dest)
            else:
                shutil.copy2(path, dest)

    def write(path, text, private=False):
        if path.exists() and path.read_text() == text:
            return
        save(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".install-tmp")
        temp.write_text(text)
        if private:
            temp.chmod(0o600)
        temp.replace(path)
        changed.append(str(path))

    def link(path, source):
        if path.is_symlink() and path.resolve() == source.resolve():
            return
        save(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir() and not path.is_symlink():
            # Move the old directory to the already-created backup instead of deleting it.
            shutil.move(str(path), str(backup / (path.name + "-original")))
        elif path.exists() or path.is_symlink():
            path.unlink()
        path.symlink_to(source)
        changed.append(str(path))

    live = home / ".codex"
    baseline = tomllib.loads((ROOT / "config.toml").read_text())
    config = live / "config.toml"
    text = config.read_text() if config.exists() else ""
    original = tomllib.loads(text)
    for key, value in baseline.items():
        if isinstance(value, dict):
            for k, v in value.items():
                text = merge_setting(text, key, k, v)
        else:
            text = merge_setting(text, "", key, value)
    parsed = tomllib.loads(text)
    for key in ("projects", "model", "model_reasoning_effort"):
        if key in original:
            assert parsed[key] == original[key], "Machine settings changed"
    write(config, text, private=True)
    link(live / "dotfiles", ROOT)
    link(live / "AGENTS.md", ROOT / "AGENTS.md")
    for name in ("consult", "handoff"):
        link(home / ".agents/skills" / name, ROOT / "skills" / name)
    humanizer = ROOT.parent / "shared/skills/humanizer"
    link(home / ".agents/skills/humanizer", humanizer)
    link(home / ".claude/skills/humanizer", humanizer)

    path = live / "hooks.json"
    hooks = json.loads(path.read_text()) if path.exists() else {"hooks": {}}
    events = hooks.setdefault("hooks", {})
    for event, filename, matcher in (
        ("PreToolUse", "gh-account-guard.py", "^Bash$"),
        ("SessionStart", "session-start.py", "startup|resume|clear|compact"),
    ):
        command = shlex.join([sys.executable, str(live / "dotfiles/hooks" / filename)])
        groups = events.setdefault(event, [])
        # Replace only handlers owned by this installer; preserve unrelated hooks.
        for group in groups:
            group["hooks"] = [h for h in group.get("hooks", [])
                              if str(live / "dotfiles/hooks" / filename) not in h.get("command", "")]
        groups[:] = [g for g in groups if g.get("hooks")]
        groups.append({"matcher": matcher, "hooks": [{"type": "command", "command": command,
                       "timeout": 15, "statusMessage": "Checking GitHub account" if event == "PreToolUse" else "Loading saved context"}]})
    write(path, json.dumps(hooks, indent=2) + "\n", private=True)

    if migrate_memory:
        memory = home / ".config/codex-private-memory"
        memory.mkdir(parents=True, exist_ok=True, mode=0o700)
        entries = []
        reference_notes = []
        global_slug = re.sub(r"[^A-Za-z0-9]", "-", str(home))
        source = home / ".claude/projects"
        for directory in sorted(source.glob("*/memory")):
            slug = directory.parent.name
            if slug == global_slug:
                scope = None
            else:
                matches = [p for tree in (home / "work", home / "personal") if tree.exists()
                           for p in tree.iterdir() if p.is_dir() and re.sub(r"[^A-Za-z0-9]", "-", str(p)) == slug]
                if len(matches) != 1:
                    continue
                scope = str(matches[0])
            for note in sorted(directory.glob("*.md")):
                if note.name == "MEMORY.md":
                    continue
                dest = memory / "imported" / slug / note.name
                write(dest, note.read_text(), private=True)
                # Long machine history stays available on demand, not injected every turn.
                if note.name not in ("mac-dev-environment-setup.md", "mac-window-utility-apps.md"):
                    entries.append({"file": str(dest.relative_to(memory)), "scope": scope})
                else:
                    reference_notes.append(str(dest))
        if reference_notes:
            pointer = memory / "machine-notes.md"
            write(pointer, "# Historical machine notes\n\nRead these only for machine setup questions. Recheck historical facts before acting.\n"
                  + "\n".join("- " + name for name in reference_notes) + "\n", private=True)
            entries.append({"file": "machine-notes.md", "scope": None})
        index = memory / "index.json"
        existing = json.loads(index.read_text()) if index.exists() else []
        imported_files = {e["file"] for e in entries}
        entries = [e for e in existing if e["file"] not in imported_files] + entries
        write(index, json.dumps(entries, indent=2) + "\n", private=True)

    if ponytail:
        subprocess.run(["codex", "plugin", "marketplace", "add", "DietrichGebert/ponytail",
                        "--ref", PONYTAIL_REF], check=True)
        subprocess.run(["codex", "plugin", "add", "ponytail@ponytail"], check=True)
    print(json.dumps({"changed": changed, "backup": str(backup) if backup.exists() else None}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home", type=Path, default=Path.home(), help="Target home (also useful for offline installation tests)")
    p.add_argument("--with-ponytail", action="store_true")
    p.add_argument("--migrate-memory", action="store_true", help="Import existing local Claude memory, preserving project scopes")
    args = p.parse_args()
    if args.with_ponytail and args.home.resolve() != Path.home().resolve():
        p.error("Ponytail installation requires the actual home directory")
    install(args.home.resolve(), args.with_ponytail, args.migrate_memory)
