# dotfiles

The new [Codex setup](codex/README.md) lives in `codex/`. Its portable config and
Consult roster are separate from Claude.

Personal configuration files for macOS, Windows, and Linux machines.

## Structure

```
dotfiles/
├── .claude-plugin/
│   └── marketplace.json         - Claude Code plugin marketplace for this repo
├── claude/
│   ├── CLAUDE.md                - global Claude Code conventions
│   │                              (symlink ~/.claude/CLAUDE.md to this)
│   └── plugins/
│       ├── consult/             - Claude Code plugin: /consult:2nd + /consult:panel
│       │                          (second opinions from independent models via OpenRouter)
│       └── handoff/             - Claude Code plugin: /handoff:handoff + SessionStart hook
│                                  (HANDOFF.md session resume memory for cold starts)
├── windows/
│   ├── vscode/
│   │   ├── settings.json          - VS Code preferences
│   │   ├── keybindings.json       - keyboard shortcuts
│   │   ├── extensions-local.txt   - extensions installed on Windows (Remote SSH, GitLens, etc.)
│   │   ├── extensions-wsl.txt     - extensions installed inside WSL Ubuntu (Python stack, Claude Code, etc.)
│   │   └── snippets/              - custom code snippets (if any)
│   ├── claude/
│   │   └── statusline-command.py - Claude Code status line script (model, ctx%, cost, rate limits)
│   └── scripts/
│       ├── setup.ps1            - run once on a new Windows machine to apply all configs
│       └── update-extensions.ps1 - updates extensions only if N days have passed since release
└── codex/
    ├── AGENTS.md                - link to shared claude/CLAUDE.md
    ├── config.toml              - portable settings; no model defaults
    ├── consult/advisors.toml    - Codex-only Consult roster
    ├── README.md                - setup and ownership guide
    ├── PLAN.md                  - implementation status
    └── DECISIONS.md             - setup decisions
```

## Claude Code plugins

This repo doubles as a Claude Code plugin marketplace:

```
/plugin marketplace add parthkulshreshtha/dotfiles
```

| Plugin | Install | What it does |
|---|---|---|
| `consult` | `/plugin install consult@parth-dotfiles` | `/consult:2nd` (one independent second opinion) and `/consult:panel` (a panel of independent model advisors), backed by OpenRouter. [Docs](claude/plugins/consult/README.md). |
| `handoff` | `/plugin install handoff@parth-dotfiles` | `/handoff:handoff` saves the session state to `HANDOFF.md`; a SessionStart hook injects it into the next session so cold starts resume with zero context. [Docs](claude/plugins/handoff/README.md). |

## How to use on a new Windows machine

1. Install VS Code (user scope, no admin needed):
   ```
   winget install --id Microsoft.VisualStudioCode --scope user --silent
   ```

2. Clone this repo:
   ```
   git clone git@github-personal:parthkulshreshtha/dotfiles.git
   ```

3. Run setup (copies settings, installs extensions):
   ```
   .\dotfiles\windows\scripts\setup.ps1
   ```

## How to use on a new macOS machine

The Claude Code status line is the only piece wired up on macOS so far.

1. Clone this repo to `~/personal/dotfiles`.

2. Add a `statusLine` block to `~/.claude/settings.json` pointing at the script in the repo:
   ```json
   "statusLine": {
     "type": "command",
     "command": "/opt/homebrew/bin/python3 /Users/<you>/personal/dotfiles/windows/claude/statusline-command.py",
     "padding": 0
   }
   ```
   Use an absolute interpreter path — the status line runs in a non-login shell, so Homebrew's
   `/opt/homebrew/bin` is not guaranteed to be on `PATH`. `/usr/bin/python3` works too; the script
   is stdlib-only.

3. Sanity-check it without launching Claude Code:
   ```
   echo '{"model":{"display_name":"Opus 5"},"cost":{"total_cost_usd":0.1}}' \
     | python3 windows/claude/statusline-command.py
   ```

## Updating extensions

Run manually whenever you want to update — only updates extensions released more than N days ago (configured inside the script):

```
.\dotfiles\windows\scripts\update-extensions.ps1
```

## What goes where

| File | What to edit it for |
|---|---|
| `windows/vscode/settings.json` | Editor preferences, theme, font, language-specific settings |
| `windows/vscode/keybindings.json` | Custom keyboard shortcuts |
| `windows/vscode/extensions-local.txt` | Add/remove extensions for the Windows VS Code client |
| `windows/vscode/extensions-wsl.txt` | Add/remove extensions for the WSL Ubuntu VS Code server |
| `windows/scripts/setup.ps1` | Change where files get copied, add new tools to install |
| `windows/scripts/update-extensions.ps1` | Change the day threshold (default: 7 days) |
| `windows/claude/statusline-command.py` | Add/remove sections in the Claude Code status line |
| `codex/config.toml` | Portable Codex settings and status-line segments; no model defaults |
| `codex/consult/advisors.toml` | Consult reviewer models, routes, and panels |

## Notes

- SSH config is NOT tracked here — too many machine-specific paths and server IPs.
  Keep a sanitized `ssh/config.example` if needed in future.
- Extension binaries are not tracked — only the ID lists in `extensions-local.txt` and `extensions-wsl.txt`.
  The setup script installs them fresh from the marketplace.
- The two status lines are wired up differently:
  - **Claude Code** runs its script straight out of this repo — `~/.claude/settings.json` points at
    it directly (`python3 /home/parth/dotfiles/...` under WSL,
    `/opt/homebrew/bin/python3 /Users/<you>/personal/dotfiles/...` on macOS). Editing the file here
    takes effect immediately, no copy step.
  - **Codex** has a portable baseline in `codex/config.toml`, verified against the live config.
    Merge it into `~/.codex/config.toml`, preserving machine-local trust and app settings.
    See [Codex setup](codex/README.md) for installation status.
- `windows/claude/` is a historical location; that script is platform-agnostic (pure stdlib Python)
  and actually runs under WSL and on macOS.
