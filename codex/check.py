#!/usr/bin/env python3
"""Offline checks for installation, routing, hook behavior, and scoped context."""
import argparse
import contextlib
import importlib.util
import io
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def guard(command, cwd, **extra):
    result = subprocess.run([sys.executable, str(ROOT / "hooks/gh-account-guard.py")],
                            input=json.dumps({"cwd": str(cwd), "tool_input": {"command": command, **extra}}),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout).get("hookSpecificOutput", {}) if result.stdout else {}


def main():
    home = Path.home()
    for tree in ("personal", "work"):
        result = guard("gh api user", home / tree)
        assert result["permissionDecision"] == "allow"
        assert ".config/gh-" + tree in result["updatedInput"]["command"]
        assert "unset GH_TOKEN GITHUB_TOKEN" in result["updatedInput"]["command"]
    assert guard("gh api user", "/tmp")["permissionDecision"] == "deny"
    assert guard("cd ~/personal && gh api user; cd ~/work && gh api user", home)["permissionDecision"] == "deny"
    assert "gh-personal" in guard("cd ~/personal && gh api user", home)["updatedInput"]["command"]
    assert "gh-personal" in guard("/opt/homebrew/bin/gh api user", home, workdir=str(home / "personal"))["updatedInput"]["command"]
    assert guard("gh --version", "/tmp") == {}
    assert guard("gh --version; gh api user", "/tmp")["permissionDecision"] == "deny"
    assert guard("GH_CONFIG_DIR=/tmp/explicit gh api user", "/tmp") == {}
    assert guard("echo safe", "/tmp") == {}
    bad = subprocess.run([sys.executable, str(ROOT / "hooks/gh-account-guard.py")], input="{", text=True, capture_output=True)
    assert bad.returncode == 2

    installer = module("installer", ROOT / "install.py")
    session = module("session", ROOT / "hooks/session-start.py")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        (target / ".codex").mkdir()
        config = target / ".codex/config.toml"
        config.write_text('model = "chosen-model"\n[tui]\nstatus_line = ["old"]\n[tui.model_availability_nux]\nkeep = 3\n[projects."/test"]\ntrust_level = "trusted"\n')
        notes = target / '.claude/projects' / re.sub(r'[^A-Za-z0-9]', '-', str(target)) / 'memory'
        notes.mkdir(parents=True)
        (notes / 'preference.md').write_text('Imported preference')
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(target, migrate_memory=True)
        index = json.loads((target / '.config/codex-private-memory/index.json').read_text())
        assert len(index) == 1 and index[0]['scope'] is None
        first = config.read_text()
        parsed = tomllib.loads(first)
        assert parsed["model"] == "chosen-model"
        assert parsed["projects"]["/test"]["trust_level"] == "trusted"
        assert parsed["tui"]["model_availability_nux"]["keep"] == 3
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(target)
        assert config.read_text() == first
        hooks = json.loads((target / ".codex/hooks.json").read_text())
        assert len(hooks["hooks"]["SessionStart"]) == 1
        assert (target / ".agents/skills/humanizer/SKILL.md").is_file()
        assert (target / ".claude/skills/humanizer").resolve() == (target / ".agents/skills/humanizer").resolve()
        memory = target / "private"
        memory.mkdir()
        (memory / "global.md").write_text("GLOBAL_NOTE")
        (memory / "scoped.md").write_text("SCOPED_NOTE")
        work = target / "work"
        work.mkdir()
        (memory / "index.json").write_text(json.dumps([
            {"file": "global.md", "scope": None}, {"file": "scoped.md", "scope": str(work)}]))
        (work / "HANDOFF.md").write_text("# HANDOFF - example\nRESUME_MARKER")
        assert "SCOPED_NOTE" not in session.context(target, memory)
        assert "GLOBAL_NOTE" in session.context(target, memory)
        assert "SCOPED_NOTE" in session.context(work, memory)
        assert "RESUME_MARKER" in session.context(work, memory)

    consult = module("consult_adapter", ROOT / "consult/consult.py")
    verdict = dict(verdict="AGREE", headline="Valid", issues=[], alternative="", confidence="HIGH", what_would_change_my_mind="New evidence")
    def fake_run(command, **kwargs):
        assert command[0:2] == ["codex", "exec"]
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert kwargs["env"]["CODEX_CONSULT_ACTIVE"] == "1"
        Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(verdict))
        return subprocess.CompletedProcess(command, 0)
    roster = tomllib.loads((ROOT / "consult/advisors.toml").read_text())
    args = argparse.Namespace(lens=None, panel="code", question="Review", web=False)
    with patch.object(consult.subprocess, "run", fake_run), patch.object(consult.helper, "call_seat", side_effect=AssertionError("GPT sent to OpenRouter")):
        for name in ("sol", "codex", "astra"):
            record = consult.review(name, roster["seats"][name], roster, args, "artifact", None)
            assert record["ok"] and record["provider"] == "Codex"
    with patch.object(consult, "codex_review", side_effect=AssertionError("Fable sent to Codex")), patch.object(consult.helper, "call_seat", return_value={"ok": True, "verdict_obj": verdict}):
        assert consult.review("fable", roster["seats"]["fable"], roster, args, "artifact", None)["ok"]
    with patch.object(consult.helper, "call_seat", return_value={"ok": False, "error": "SECRET_ARTIFACT"}):
        assert "SECRET_ARTIFACT" not in consult.review("fable", roster["seats"]["fable"], roster, args, "artifact", None)["error"]
    print("PASS: account routing, hook deny/rewrite, scoped context, installer idempotence, preserved settings, shared skill links, Codex/OpenRouter separation")


if __name__ == "__main__":
    main()
