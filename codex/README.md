# Codex dotfiles

This directory owns the Codex setup. Shared global instructions are installed.
Live settings match the portable baseline. Remaining integrations are not installed;
see PLAN.md.

## Files

| Source | Purpose / eventual destination |
|---|---|
| `config.toml` | Portable settings merged into `~/.codex/config.toml` |
| `AGENTS.md` | Relative link to `../claude/CLAUDE.md`; shared global instructions |
| `consult/advisors.toml` | Codex-only review models, roles, and panels |
| `PLAN.md` | Completed work and remaining installation tasks |
| `DECISIONS.md` | Reasons for the layout and routing choices |

Keep machine trust paths, authentication, hook trust, logs, and private memory
outside version control. Merge portable settings rather than replacing the live
config: Codex also writes machine and app state there.

Humanizer will have one shared source with links from both tools. Codex plugins,
hooks, and installation scripts belong here when implemented. Do not link entire
Claude and Codex configuration directories together.

For new projects, add shared project instructions only when requested at setup.
Do not enable global fallback discovery of `CLAUDE.md`.

## Consult roster

| Panel | Reviewers |
|---|---|
| `code` | Sol, Terra (`codex` seat), Fable, Gemini |
| `decision` | Sol, Grok, Gemini, Fable |
| `writing` | Fable, Kimi, Sol |
| `cheap` | GLM, DeepSeek, Grok |
| `max` | Astra, Gemini, Grok 4.6 (`grok-45` seat), Kimi, Fable |

GPT seats have `kind = "subagent"`. The existing OpenRouter helper excludes
those seats from API calls and returns them as pending reviews. The Codex adapter
must run them through Codex and combine all verdicts. This roster alone does not
install or implement that adapter. Do not use the Claude command prompts with it.

Fable is pinned to `anthropic/claude-fable-5.1`. Other OpenRouter seats retain
the existing Claude roster IDs; their availability needs checking before live use.
GPT selections were checked against this machine's cached Codex model catalog.
No paid model calls have been made. Unavailable seats must fail clearly, without
silently substituting providers or models.

All model and effort settings here apply only to Consult. The main Codex session
has no model or reasoning defaults in this configuration.

The Claude plugin and its roster remain independently configured. Future sharing
should reuse helper code without sharing host-specific routing or command prompts.
