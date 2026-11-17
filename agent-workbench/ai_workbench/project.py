from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from .core import ManagedConflictError, atomic_write, managed_block_hash, read_text_exact, replace_managed_block, START_MARKER, END_MARKER

PROJECT_BLOCK = f"""{START_MARKER}
## AI Workbench

For coding, architecture, debugging, refactoring or delivery tasks, use the installed $ai-workbench skill when relevant. It is a workflow guide, not a reason to add ceremony to small changes.

- The latest user request defines active scope; retire obsolete work when the goal changes.
- Inspect the actual repository, worktree, implementation, tests, runtime and entry points before choosing an approach.
- Reuse existing components, APIs, data models and environment capabilities before creating replacements.
- Distinguish confirmed user decisions, observed implementation facts, verified outcomes, hypotheses and unknowns.
- Use current skills when their triggers apply: $writing-specs, $writing-plans, $executing-plans, $task-execution-discipline, $test-driven-development and $auditing-finding-closure.
- Keep one primary agent accountable for end-to-end completion; delegate only genuinely independent work.
- Verify the final changed state and report exact checks and remaining uncertainty.
- Maintain .ai-workbench/PROJECT_STATE.md only for durable decisions, multi-step recovery and verified project facts; keep it concise.

Do not force full-repository scans, plans, multiple agents, full test suites or extra documentation onto every small change. Preserve project conventions unless evidence shows they obstruct the required outcome.
{END_MARKER}"""

def project_state_template() -> str:
    return """# Project State

> Durable handoff facts only. Update when a decision, verified entry point, or recovery state materially changes. Do not use as a chronological command log.

## Project purpose and entry points
- Unknown — inspect the current repository before relying on assumptions.

## Confirmed architecture and decisions
- None recorded.

## Verified commands and environments
- None recorded.

## Active objective
- None.

## Unknowns and blockers
- None recorded.

## Next recovery action
- None.
"""

def initialize_project(project_root: Path) -> dict:
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Project path is not a directory: {root}")
    agents = root / "AGENTS.md"
    if agents.is_symlink():
        raise ManagedConflictError(f"Refusing to edit symlinked project instructions: {agents}")
    original = read_text_exact(agents) if agents.exists() else ""
    current_hash = managed_block_hash(original)
    state_dir = root / ".ai-workbench"
    state_file = state_dir / "PROJECT_STATE.md"
    config_file = state_dir / "config.json"
    ownership_file = state_dir / "managed.json"
    if state_dir.is_symlink() or any(p.is_symlink() for p in (state_file, config_file, ownership_file)):
        raise ManagedConflictError(f"Refusing to write through symlinked project state paths: {state_dir}")
    if ownership_file.exists():
        try:
            ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManagedConflictError(f"Cannot read project ownership record {ownership_file}: {exc}") from exc
        if current_hash is None or current_hash != ownership.get("project_agents_block_hash"):
            raise ManagedConflictError(f"Project AI Workbench instructions were removed or modified: {agents}")
        separator_added = bool(ownership.get("separator_added"))
    else:
        if current_hash is not None:
            raise ManagedConflictError(f"Existing AI Workbench markers have no ownership record: {agents}")
        separator_added = bool(original and not original.endswith("\n"))
    updated = replace_managed_block(original, PROJECT_BLOCK)
    created: list[str] = []
    if updated != original:
        atomic_write(agents, updated)
        created.append(str(agents))
    ownership_existed = ownership_file.exists()
    atomic_write(ownership_file, json.dumps({"schema_version": 1, "project_agents_block_hash": managed_block_hash(updated), "separator_added": separator_added}, indent=2) + "\n")
    if not ownership_existed:
        created.append(str(ownership_file))
    if not state_file.exists():
        atomic_write(state_file, project_state_template())
        created.append(str(state_file))
    if not config_file.exists():
        config = {"schema_version": 1, "workbench": "ai-workbench", "specs_repository": "https://github.com/wly112488/ai-specs", "initialized_at": datetime.now(timezone.utc).isoformat()}
        atomic_write(config_file, json.dumps(config, indent=2) + "\n")
        created.append(str(config_file))
    return {"project": str(root), "agents_updated": updated != original, "previous_managed_hash": current_hash, "created": created}
