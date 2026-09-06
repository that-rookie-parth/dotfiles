# Codex dotfiles

This directory owns the Codex setup. Claude keeps its own configuration and roster.
Shared global instructions and Humanizer each have one source.

## Install on a new machine

Requires Codex CLI, Python 3.11+, Node.js for Ponytail, and a Codex login.
Run from the dotfiles repository:

```sh
python3 codex/check.py
python3 codex/install.py --with-ponytail --migrate-memory
```

`--with-ponytail` installs the verified 4.9.0 source commit. Omit it when only refreshing local files.
`--migrate-memory` imports local Claude notes when available. It never downloads private notes from Git.
The installer backs up replaced files under `~/.config/codex-backups/` and is safe to rerun.
It merges owned settings while preserving machine-specific trust, plugin, and app configuration.
It adds no model or reasoning defaults and never changes project files.

Open Codex from a trusted directory. In `/hooks`, review the two local hooks and three Ponytail hooks,
then trust them. Start a new session after installation. Hook trust is local and is not copied between machines.
Do not bypass hook trust. Review hooks again if Codex reports them changed.

## Files and live locations

| Source | Live location / purpose |
|---|---|
| `config.toml` | Portable values merged into `~/.codex/config.toml` |
| `AGENTS.md` | Link to `../claude/CLAUDE.md`, installed as `~/.codex/AGENTS.md` |
| This directory | Linked at `~/.codex/dotfiles` for stable script paths |
| `skills/consult`, `skills/handoff` | Linked under `~/.agents/skills/` |
| `../shared/skills/humanizer` | Linked under both `~/.agents/skills/` and `~/.claude/skills/` |
| `consult/advisors.toml` | Codex-only reviewer models, roles, and panels |
| `consult/consult.py` | Executes complete reviews; reuses Claude's OpenRouter transport code |
| `hooks/gh-account-guard.py` | GitHub account routing via `~/.codex/hooks.json` |
| `hooks/session-start.py` | Loads handoffs and private scoped notes via `~/.codex/hooks.json` |
| `install.py`, `check.py` | Repeatable setup and offline checks |

Credentials, private memory, review logs, hook trust, and machine paths stay outside version control.
For new projects, add shared project instructions only when requested at setup.
There is no global `CLAUDE.md` fallback discovery.

## Consult

Invoke `$consult` with a second-opinion request or ask for a named panel.
You can also call the helper directly:

```sh
python3 ~/.codex/dotfiles/consult/consult.py --list
python3 ~/.codex/dotfiles/consult/consult.py --panel code --question 'Review this diff' --artifact /path/to/diff.txt
python3 ~/.codex/dotfiles/consult/consult.py --seat fable --question 'Review this proposal' --artifact /path/to/proposal.txt
python3 ~/.codex/dotfiles/consult/consult.py --check
```

| Panel | Reviewers |
|---|---|
| `code` | Sol, Terra (`codex` seat), Fable, Gemini |
| `decision` | Sol, Grok, Gemini, Fable |
| `writing` | Fable, Kimi, Sol |
| `cheap` | GLM, DeepSeek, Grok |
| `max` | Astra, Gemini, Grok 4.6 (`grok-45` seat), Kimi, Fable |

GPT seats use separate read-only `codex exec` sessions with explicit models and structured verdicts.
They never route through OpenRouter. Fable is pinned to `anthropic/claude-fable-5.1` through OpenRouter.
Other families retain the existing OpenRouter roster. The adapter runs panel members concurrently.
Model and effort settings apply only to Consult, not the main session.

OpenRouter uses `OPENROUTER_API_KEY` or `~/.config/openrouter/key`, including the existing key rotation.
Codex uses its own existing login. OpenRouter credit and Codex usage are separate.
The rendered dollar total covers OpenRouter calls only; Codex records have no dollar estimate.
No provider/model substitutions happen automatically. Exit 2 means incomplete results; exit 3 means exhausted API keys.
API failures are reported without raw provider bodies. Usage logs contain metadata only,
at `~/.local/state/codex-consult/usage.jsonl` (or `$XDG_STATE_HOME/codex-consult/usage.jsonl`).
The skill keeps its decision notes outside Git at `~/.local/state/codex-consult/decisions/`.

## Handoff and memory

Use `$handoff` before ending or clearing a session. It writes a bounded `HANDOFF.md` without committing it.
The startup hook reads files beginning with `# HANDOFF` and includes a fresh Git status check.
It also accepts existing Claude handoff files.

Imported notes live in `~/.config/codex-private-memory/`. `index.json` controls scope:
`null` means global; an absolute directory applies only there and below it.
Long machine notes are available through a short pointer, rather than injected into every session.
Project-specific approval preferences remain scoped to their original project.
These readable notes complement Codex's enabled native memory; its internal memory database is not edited.

## GitHub guard

Bare `gh` calls under `~/personal` use `~/.config/gh-personal`; those under `~/work` use `~/.config/gh-work`.
Named tree paths take precedence over the command working directory. Mixed or missing trees are denied.
Automatic routing clears inherited `GH_TOKEN` and `GITHUB_TOKEN` overrides.
Explicit `GH_CONFIG_DIR` assignments are preserved. Version/help calls need no account.
This is a command-pattern guard, not a complete shell parser. Use explicit account selection for complex shell wrappers.
Existing Git credential helpers remain independently configured.

## Ponytail and status line

Ponytail 4.9.0 is installed from `DietrichGebert/ponytail` at commit `2ed6c52c9d7e5e56942508591085fd45dea277d3`.
Its skills appear in `/skills`, including `$ponytail:ponytail`, `$ponytail:ponytail-review`, and the audit/debt/gain/help skills.
Use `$ponytail:ponytail lite`, `full`, `ultra`, or `off` to switch modes.
Its session state uses Codex plugin data. Ponytail's persistent default configuration is shared across hosts by the upstream plugin.

The status line keeps the existing fields and adds total input tokens, context-window size,
and `estimated-thread-cost`. The cost field is conditional on account support (the CLI labels it Enterprise-only).
There is no custom Ponytail badge field. Voice settings are unchanged.

## Validation

Run `python3 codex/check.py` after changing the installer, routing, or hooks.
It checks account routing, scoped notes, repeated installation, and preservation of existing settings without API calls.
Use Consult's `--check` to validate remote model IDs without running paid reviews.

Local hook behavior and persisted trust were verified during installation.
Automatic context injection on a real turn remains unverified.
