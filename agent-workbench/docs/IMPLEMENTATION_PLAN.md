# AI Workbench CLI Implementation Plan

> **For agentic workers:** Execute the tasks in order. Each task is independently testable. Preserve the source audit records.

**Goal:** Deliver a cross-platform `aiw` CLI that installs current ai-specs skills and managed Codex instructions, initializes projects, diagnoses health, and launches the existing Codex CLI safely.

**Architecture:** A Python 3.10+ standard-library CLI with platform-aware paths, hash-managed installation, a private ai-specs checkout, a project initializer, read-only diagnostics, and a thin Codex launcher. The product lives in an isolated `agent-workbench/` subproject so the historical audit corpus remains intact.

**Tech Stack:** Python 3.10+, unittest, Git CLI, Codex CLI; no third-party runtime dependencies.

**Spec:** `agent-workbench/SPEC.md`

## Global Constraints

- `wly112488/ai-specs` remains the source of truth for execution specs and skills.
- Do not modify, delete, weaken, defer, or reclassify existing confirmed findings.
- Never overwrite user-owned or user-modified AGENTS/skill files silently.
- Never change Codex authentication, model, sandbox or approval settings.
- Never launch Codex with security-bypass or unattended full-auto flags.
- Keep Windows and WSL support in one Python implementation.
- Behavior-changing production code follows RED-GREEN-REFACTOR; behavior-preserving refactors preserve existing green coverage.
- Use only Python standard library at runtime.

---

## Implementation Roadmap

This is one cohesive deliverable because the installer, managed state, project initializer, health checks and launcher share one ownership manifest and must be validated together.

## File Structure

- Create: `agent-workbench/aiw.py` — CLI entrypoint and command dispatch.
- Create: `agent-workbench/ai_workbench/__init__.py` — version.
- Create: `agent-workbench/ai_workbench/core.py` — paths, manifest, hashes, atomic I/O, marker management.
- Create: `agent-workbench/ai_workbench/specs.py` — private specs clone/update and skill mapping.
- Create: `agent-workbench/ai_workbench/project.py` — idempotent project initialization and state template.
- Create: `agent-workbench/ai_workbench/commands.py` — install/update/status/doctor/uninstall/launch.
- Create: `agent-workbench/skills/ai-workbench/SKILL.md` — runtime collaboration mechanism.
- Create: `agent-workbench/tests/test_core.py`, `test_specs.py`, `test_project.py`, `test_cli.py`.
- Create: `agent-workbench/README.md`, `agent-workbench/SECURITY.md`, `agent-workbench/pyproject.toml` (if packaging is retained).
- Modify: root `README.md` only to add an accurate link describing the separate runtime subproject.

## Task 1: Define and test path/managed-file primitives

**Files:** core.py, tests/test_core.py

**Interfaces:**
- `get_paths(env=None, platform=None, home=None) -> Paths`
- `sha256_text(text) -> str`
- `replace_managed_block(existing, start_marker, end_marker, block) -> str`
- `atomic_write(path, text) -> None`
- manifest read/write helpers.

**Acceptance:**
- Platform-specific paths are deterministic and testable without touching the real home.
- Existing unmanaged content is byte-for-byte preserved.
- Marker replacement is idempotent and rejects malformed/duplicate markers.
- Atomic writes leave the prior file intact on failure.
- Hash comparison identifies user edits.

- [ ] Step 1: Write failing unit tests for platform path selection, marker insertion/replacement, malformed markers, hash changes and atomic write.
- [ ] Step 2: Run the targeted tests and observe expected failures.
- [ ] Step 3: Implement only the primitives needed by those tests.
- [ ] Step 4: Re-run targeted tests and preserve green coverage.
- [ ] Step 5: Run `git diff --check`.

## Task 2: Specs checkout and skill synchronization

**Files:** specs.py, tests/test_specs.py

**Interfaces:**
- `ensure_specs_checkout(specs_dir, repo_url, runner) -> SpecsInfo`
- `load_skill_sources(specs_root) -> dict[str, str]`
- `sync_managed_skills(skill_sources, skill_root, manifest) -> SyncResult`

**Acceptance:**
- Clone uses Git argument arrays, not shell interpolation.
- Existing clean checkout updates only via fast-forward; dirty checkout is preserved and reported.
- Required source files are validated before any skill install.
- Current skills are copied to named SKILL.md folders and upstream commit is recorded.
- Conflicts with unowned or modified skills are preserved and reported.

- [ ] Step 1: Write failing tests using temporary local Git repositories and injected subprocess runner.
- [ ] Step 2: Verify RED.
- [ ] Step 3: Implement checkout validation and mapping.
- [ ] Step 4: Verify clone, fast-forward, dirty-checkout, missing-source and skill-conflict tests.
- [ ] Step 5: Run `git diff --check`.

## Task 3: Global instruction installation and safe lifecycle

**Files:** core.py, commands.py, tests/test_core.py, tests/test_cli.py

**Interfaces:**
- `install_global_instructions(block, codex_agents_path, manifest) -> Result`
- `install_launcher(source, bin_dir, platform) -> Result`
- `uninstall_managed(manifest, paths) -> Result`

**Acceptance:**
- Existing global AGENTS content outside the managed block is preserved.
- User-edited managed blocks/files are not overwritten or deleted.
- Launcher is installed to a user bin directory with correct platform shim.
- Manifest records managed hashes and source commit.
- Uninstall is hash-guarded.

- [ ] Step 1: Write failing lifecycle tests.
- [ ] Step 2: Verify RED.
- [ ] Step 3: Implement safe install/update/uninstall.
- [ ] Step 4: Verify conflict and preservation behavior.
- [ ] Step 5: Run `git diff --check`.

## Task 4: Project initializer and durable state

**Files:** project.py, tests/test_project.py

**Interfaces:**
- `initialize_project(project_root) -> InitResult`
- `project_agents_block() -> str`
- `project_state_template() -> str`

**Acceptance:**
- Project AGENTS is extended idempotently without changing unmanaged content.
- `.ai-workbench/PROJECT_STATE.md` and config are created only if absent.
- Existing project state is never overwritten.
- Path validation prevents initializing a non-directory or ambiguous path.

- [ ] Step 1: Write failing project-init tests.
- [ ] Step 2: Verify RED.
- [ ] Step 3: Implement initializer.
- [ ] Step 4: Verify repeated init and preservation.
- [ ] Step 5: Run `git diff --check`.

## Task 5: Doctor, status, launch and CLI behavior

**Files:** commands.py, aiw.py, tests/test_cli.py

**Interfaces:**
- `doctor(paths, runner) -> list[Check]`
- `status(paths) -> Status`
- `launch_codex(project_root, args, runner) -> int`
- `main(argv=None) -> int`

**Acceptance:**
- Doctor is read-only and reports each prerequisite independently.
- Missing Codex/Git/specs prerequisites have actionable messages.
- Launch uses the selected cwd, forwards args exactly and does not inject permission flags.
- CLI exit codes distinguish success, user/configuration error and external command failure.
- No args launches interactive Codex from current directory.

- [ ] Step 1: Write failing tests with fake executables/runners.
- [ ] Step 2: Verify RED.
- [ ] Step 3: Implement CLI commands and launcher.
- [ ] Step 4: Verify argument forwarding, cwd, error propagation and read-only doctor.
- [ ] Step 5: Run `git diff --check`.

## Task 6: Documentation, packaging and end-to-end smoke tests

**Files:** README.md, SECURITY.md, pyproject.toml, tests/test_smoke.py, root README.md

**Acceptance:**
- Windows and WSL commands are exact and independently documented.
- Private specs authentication and local checkout fallback are documented.
- Security model and uninstall behavior are documented.
- Smoke test uses only temporary directories and fake Codex executable.
- Python test suite passes and source files compile.
- Root audit corpus is unchanged except its README runtime link.

- [ ] Step 1: Write failing smoke tests for install → init → doctor → launch → update → uninstall using temp dirs/local git.
- [ ] Step 2: Verify RED.
- [ ] Step 3: Implement docs and remaining integration.
- [ ] Step 4: Run all tests, compile check, clean clone-style smoke test.
- [ ] Step 5: Inspect targeted diff and confirm audit source directories are unchanged.
- [ ] Step 6: Commit the completed implementation to the feature branch and open a PR to main.
