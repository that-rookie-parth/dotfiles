---
name: handoff
description: Save current work to HANDOFF.md when the user wants to leave, clear, compact, or resume work across sessions.
---

# Handoff

Read the current handoff, Git status, five recent commits, and relevant plan and decision files.
Use the repository root, or the session directory outside Git.
Overwrite `HANDOFF.md` with current state, never append. Do not overwrite an unrelated file
whose first line does not start with `# HANDOFF`.

Keep at most 80 lines, preferably 40. Start with `# HANDOFF - <project>` and use these sections:

- `Now`: project purpose, active objective, and plan orientation if a plan exists.
- `Just finished`: changes from this session, with file paths and validation.
- `Next step`: one concrete action with enough detail for a cold start.
- `Watch out`: current traps and constraints; move durable facts to project documentation when authorized.
- `Waiting on user`: unresolved choices with their options, or `Nothing.`

Every plan or decision reference includes its stable ID, plain-language meaning, and source path.
Preserve pending choices and unresolved issues. Reconcile the handoff against actual Git state.
Do not include credentials, raw sensitive data, or unrelated conversation details.
The startup hook reads this file in future sessions, including Claude's compatible handoff format.
Saving a handoff does not authorize committing or pushing it. Finish with its path and whether work can resume cleanly.
