#!/usr/bin/env python3
"""PreToolUse(Bash) guard: pin bare `gh` commands to the right GitHub account.

Git credentials are already routed by repo location (includeIf in ~/.gitconfig).
Bare `gh` commands never go through git, so they still depend on GH_CONFIG_DIR
being set by direnv - which does not happen for agent tooling. This hook closes
that gap by deciding the account from the command's target tree and prepending
the export itself.

Outside ~/personal and ~/work there is no correct account, so it denies rather
than guess. That matches the fail-closed github.com block in ~/.gitconfig.
"""
import json
import os
import re
import sys
import shlex

HOME = os.path.expanduser("~")
TREES = {"personal": "gh-personal", "work": "gh-work"}

# `gh` as an actual command: start of line, or after ; | & ( or newline,
# optionally preceded by VAR=value assignments.
GH_CALL = re.compile(r"(?:^|[\n;&|(])\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:(?:command|env)\s+)?(?:[\w./-]+/)?gh(?:\s|$)")

# Subcommands that do not depend on which account is active.
ACCOUNT_FREE = re.compile(r"\bgh\s+(?:--version|--help|-h|version|help|completion)\b")


def emit(obj):
    json.dump(obj, sys.stdout)
    sys.exit(0)


def tree_of(path):
    path = os.path.realpath(os.path.expanduser(path))
    for tree in TREES:
        root = os.path.realpath(os.path.join(HOME, tree))
        if path == root or path.startswith(root + os.sep):
            return tree
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("GitHub guard received invalid JSON", file=sys.stderr)
        sys.exit(2)

    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not GH_CALL.search(cmd):
        sys.exit(0)
    if re.search(r"(?:^|[\s;&])GH_CONFIG_DIR=", cmd):          # caller was explicit - leave it alone
        sys.exit(0)
    if re.fullmatch(r"\s*gh\s+(?:--version|--help|-h|version|help|completion)(?:\s+[^;&|\n]+)?\s*", cmd):
        sys.exit(0)

    # A path named in the command wins over cwd: agents routinely run
    # `cd ~/personal/repo && gh ...` from a different working directory.
    named = set()
    for tree in TREES:
        pat = r"(?:~|\$HOME|\{}|{})/{}(?:/|\b)".format("$HOME", re.escape(HOME), tree)
        if re.search(pat, cmd):
            named.add(tree)

    if len(named) == 1:
        tree = named.pop()
    elif len(named) > 1:
        emit({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "This `gh` command names both ~/work and ~/personal, so the account "
                "is ambiguous. Split it into two commands, or set GH_CONFIG_DIR "
                "explicitly (~/.config/gh-personal or ~/.config/gh-work)."),
        }})
    else:
        tree = tree_of((data.get("tool_input") or {}).get("workdir") or data.get("cwd") or os.getcwd())

    if not tree:
        emit({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "`gh` outside ~/personal and ~/work has no correct GitHub account, "
                "so it is blocked rather than defaulting to work. Run it from inside "
                "the right tree, or prefix it with "
                "GH_CONFIG_DIR=$HOME/.config/gh-personal (or gh-work)."),
        }})

    new_input = dict(data.get("tool_input") or {})
    new_input["command"] = 'unset GH_TOKEN GITHUB_TOKEN; export GH_CONFIG_DIR={}; {}'.format(
        shlex.quote(os.path.join(HOME, '.config', TREES[tree])), cmd)
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": new_input,
        },
    })


if __name__ == "__main__":
    main()
