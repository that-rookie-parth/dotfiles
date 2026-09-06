# consult — independent model advisors for Claude Code

Get second opinions on your plans, diffs, and decisions from a panel of
independent frontier models (GPT, Gemini, Grok, Kimi, DeepSeek, GLM, …) — without
leaving Claude Code. Transport is [OpenRouter](https://openrouter.ai), so one API
key covers every model.

Two slash commands:

| Command | What it does |
|---|---|
| `/consult:2nd <seat> <question>` | One named advisor gives one independent verdict. |
| `/consult:panel [code\|decision\|writing\|cheap\|max] <question>` | 3–5 advisors review in parallel, then Claude must decide: agreed / split / overruled / out of scope — and log the decision. |

## Why this exists

A model reviewing its own work agrees with itself. These commands send your
plan/diff/text to models from **other labs**, each with a distinct job ("lens"):
red-team, blast-radius, contrarian, conformance, prose, correctness, strategy.
The advisors never see your conversation — only a self-contained artifact — so
they can't anchor on your framing. Structured JSON verdicts
(`AGREE / AGREE_WITH_CHANGES / DISAGREE`, ranked issues, a concrete alternative
on disagreement) keep the output actionable instead of vibes.

A typical panel run costs **$0.02–$0.30** depending on panel and artifact size.
The `fable` seat runs as a Claude Code subagent on your existing Claude plan, so
it costs nothing extra.

## Install

```
/plugin marketplace add parthkulshreshtha/dotfiles
/plugin install consult@parth-dotfiles
```

If the commands don't show up right away, restart Claude Code (or check the
install with `/plugin`). Supported platforms: macOS, Linux, and Windows via
WSL — anywhere Claude Code's bash has `python3` on `PATH`.

## Setup

1. **Requirements:** Python 3.11+ (`tomllib` is stdlib from 3.11) on `PATH` as
   `python3`. No third-party packages.

2. **OpenRouter API key** — create one at
   [openrouter.ai/keys](https://openrouter.ai/settings/keys), add credit, then
   configure it in either place (env wins; both may hold several keys, tried in
   order):

   ```bash
   export OPENROUTER_API_KEY=sk-or-...        # or OPENROUTER_API_KEY_2..9 for spares
   # or
   mkdir -p ~/.config/openrouter
   echo 'sk-or-...' >> ~/.config/openrouter/key   # one key per line
   chmod 600 ~/.config/openrouter/key
   ```

3. **Sanity check** (from the plugin directory, or use the full path Claude
   shows when running the commands):

   ```bash
   bin/consult --list          # seats, panels, lenses
   bin/consult --check-keys    # credit remaining on each key
   bin/consult --check         # validate roster model slugs against the live catalog
   ```

## Usage

```
/consult:2nd grok is sticking with a monolith the wrong call for this project?
/consult:2nd sol --lens blast-radius review this migration plan
/consult:panel code review the attached refactor of the auth middleware
/consult:panel decision should we migrate from GitHub to Azure DevOps?
/consult:panel cheap does this regex handle the edge cases?
```

The `panel` command ends with a forced decision: what every advisor agreed on,
where they split (and Claude's call on each split), which findings were
overruled and why, and what was out of scope. It then logs the decision to
`~/.claude/decisions/<repo-name>.md` — outside the repo on purpose, so business
and career decisions never end up committable.

## Seats and panels

Defined in [`advisors.toml`](advisors.toml) — the script itself holds no model
names. Bundled defaults:

| Panel | Seats | Use for |
|---|---|---|
| `code` | sol, codex, fable | implementation, diffs, architecture |
| `decision` | sol, grok, gemini, fable | should-we-do-X, strategy calls |
| `writing` | fable, kimi, sol | posts, docs, comms |
| `cheap` | glm, deepseek, grok | quick sanity check, ~2 cents |
| `max` | astra, gemini, grok-45, kimi, fable | irreversible: migrations, auth, public APIs |

Seats with `web = "native"` search the web on their own initiative (model-driven
queries only — OpenRouter's exa fallback is deliberately never used because it
searches on the raw artifact and injects unrelated results). Offline seats
answer from training data, so don't send them version- or price-sensitive
questions.

## Customising the roster

The roster is resolved in this order:

1. `$CONSULT_ROSTER` — explicit path, wins always
2. `~/.claude/advisors.toml` — your personal copy (honors `$CLAUDE_CONFIG_DIR`
   if you have moved your Claude config)
3. The `advisors.toml` bundled with this plugin — the default

To customise, copy the bundled file to `~/.claude/advisors.toml` and edit it
there. Plugin updates then never clobber your changes. Model slugs go stale as
providers ship new versions — run `bin/consult --check` occasionally; it flags
stale slugs and suggests near-matches from the live catalog.

## Notes

- **`fable` seat:** runs as a Claude Code subagent (`model: fable`), not through
  OpenRouter. If your plan has no Fable access, swap the seat's `model` in the
  roster for one you have (e.g. `opus` or `sonnet`), or replace the seat.
- **Key rotation:** a key is retired mid-run on 402 (out of credit) or 401
  (revoked) and the next key takes over. 429 rate limits do *not* rotate. When
  every key is dead the run exits with code 3 and the commands are instructed to
  stop rather than fake a review. Keys on the same OpenRouter account share one
  balance — `--check-keys` warns when it detects this.
- **Telemetry:** each call appends one line (seat, cost, tokens, verdict — first
  200 chars of the question, never the artifact) to `~/.claude/consult-log.jsonl`
  so you can review cost and usage later. Delete or truncate freely.
- **Privacy:** artifacts are sent to the model providers behind OpenRouter. Set
  `data_collection = "deny"` in the roster's `[defaults]` to avoid providers
  that may train on your data. Don't send secrets in artifacts.

## Files

```
consult/
├── .claude-plugin/plugin.json   # plugin manifest
├── commands/2nd.md              # /consult:2nd
├── commands/panel.md            # /consult:panel
├── bin/consult                  # Python script: fan-out, key rotation, rendering
├── advisors.toml                # default roster: seats, panels, lenses
└── README.md
```
