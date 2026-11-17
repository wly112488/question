# Security model

## Scope

AI Workbench installs user-level Codex instructions and skills, initializes explicitly selected project directories, checks installation health, and launches the existing Codex CLI. It does not run an independent agent, install privileged services, or change Codex's approval/sandbox policy.

## Credentials

- No GitHub token, SSH private key, Codex credential, API key or OAuth token is read into AI Workbench state or written to its manifest.
- Private ai-specs access uses the user's existing Git credential manager or SSH agent.
- Git commands are invoked as argument arrays, not interpolated shell strings. Terminal prompting is disabled for Git subprocesses so a missing credential fails rather than hanging on a terminal prompt.
- Do not place credentials in --specs-dir, project config, AGENTS.md, shell history or issue reports.

## Installation trust boundary

- The authoritative skills are fetched from https://github.com/wly112488/ai-specs and the main branch.
- Existing checkouts must have the expected remote, be on main, and be clean before update. Update is fast-forward-only.
- Installation reads skill/spec text and copies it into the Codex skill directory; it does not execute scripts from the specs repository.
- Treat changes to the private ai-specs repository as changes to instructions consumed by your local coding agent. Review those changes with the same care as executable code.

## Filesystem safety

- Global instructions are managed only between explicit markers in ~/.codex/AGENTS.md.
- Project instructions are managed only between explicit markers in the selected project's root AGENTS.md.
- Existing text outside managed markers is preserved.
- SHA-256 hashes in the local install manifest detect edits to managed files. Modified or unowned targets are not overwritten or deleted silently.
- Installation snapshots affected files and attempts rollback if a write fails.
- doctor is read-only. init writes only the selected project's documented files. uninstall removes only unchanged global/launcher files and does not crawl projects.

## Codex permissions

The launcher forwards arguments to the user's existing codex executable. It does not inject full-auto, danger-full-access, approval-bypass or sandbox-bypass flags. Do not add such flags to shell aliases unless you deliberately accept the corresponding risk.

## Reporting a security issue

Do not publish credentials, private logs or unredacted Codex transcripts in public issues. Rotate any credential that may have been exposed before investigating the logs.
