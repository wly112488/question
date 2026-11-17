from __future__ import annotations
import os, re, subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from .core import ManagedConflictError, WorkbenchError, sha256_text

REPO_URL = "https://github.com/wly112488/ai-specs.git"
SKILL_MAP = {
    "task-execution-discipline": "execution-specs/task-execution-discipline",
    "executing-plans": "execution-specs/executing-plans",
    "executing-dependent-plans": "execution-specs/executing-dependent-plans",
    "test-driven-development": "execution-specs/test-driven-development",
    "auditing-finding-closure": "auditing-finding-closure",
    "writing-plans": "writing-plans",
    "writing-specs": "writing-specs",
}
RULE_HEADER = """---
name: rule-maintenance
description: Use when changing an execution spec or durable AI workflow rule.
---

Read the current authoritative RULE_MAINTENANCE_SPEC.md from the installed ai-specs checkout before changing execution specs. Its location is recorded in the AI Workbench manifest as specs_dir. Apply the smallest-safe-change, dependency, conflict and validation requirements. Do not maintain a second source-of-truth copy.

"""

@dataclass(frozen=True)
class SpecsInfo:
    root: Path
    commit: str
    remote: str

def _invoke(args: list[str], cwd: Path | None, runner: Callable | None):
    if runner:
        return runner(args, cwd=cwd)
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(args, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False, timeout=180, env=env)
    except subprocess.TimeoutExpired as exc:
        raise WorkbenchError(f"Git operation timed out after 180 seconds: {' '.join(args)}") from exc

def _output(args: list[str], cwd: Path | None = None, runner: Callable | None = None) -> str:
    result = _invoke(args, cwd, runner)
    if result.returncode:
        detail = (getattr(result, "stderr", "") or getattr(result, "stdout", "")).strip()
        raise WorkbenchError(f"Command failed ({result.returncode}): {' '.join(args)}\n{detail}")
    return (getattr(result, "stdout", "") or "").strip()

def _canonical_remote(value: str) -> str:
    value = value.strip().lower().replace("ssh://git@github.com/", "https://github.com/")
    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value.split(":", 1)[1]
    return value.removesuffix(".git").rstrip("/")

def ensure_specs_checkout(specs_dir: Path, repo_url: str = REPO_URL, runner: Callable | None = None, update_existing: bool = True) -> SpecsInfo:
    _output(["git", "--version"], runner=runner)
    if specs_dir.exists():
        if not (specs_dir / ".git").exists():
            raise WorkbenchError(f"Not a Git checkout: {specs_dir}. Supply a valid ai-specs clone.")
        branch = _output(["git", "branch", "--show-current"], specs_dir, runner)
        if branch != "main":
            raise WorkbenchError(f"ai-specs checkout must be on main, not {branch!r}: {specs_dir}")
        if _output(["git", "status", "--porcelain"], specs_dir, runner):
            raise WorkbenchError(f"ai-specs checkout has local changes; refusing to overwrite them: {specs_dir}")
        if update_existing:
            _output(["git", "pull", "--ff-only"], specs_dir, runner)
    else:
        specs_dir.parent.mkdir(parents=True, exist_ok=True)
        _output(["git", "clone", "--depth", "1", "--branch", "main", repo_url, str(specs_dir)], runner=runner)
    commit = _output(["git", "rev-parse", "HEAD"], specs_dir, runner)
    remote = _output(["git", "remote", "get-url", "origin"], specs_dir, runner)
    if _canonical_remote(remote) != _canonical_remote(repo_url):
        raise WorkbenchError(f"Unexpected ai-specs remote {remote!r}; expected {repo_url!r}")
    load_skill_sources(specs_dir)
    return SpecsInfo(specs_dir, commit, remote)

def load_skill_sources(specs_root: Path) -> dict[str, str]:
    sources = {}
    for name, relative in SKILL_MAP.items():
        path = specs_root / relative
        if not path.is_file():
            raise WorkbenchError(f"Required current skill is missing: {path}")
        content = path.read_text(encoding="utf-8")
        header = content.split("---", 2)[1] if content.startswith("---") and content.count("---") >= 2 else ""
        declared_name = re.search(r"(?m)^name:\s*([A-Za-z0-9_-]+)\s*$", header)
        description = re.search(r"(?m)^description:\s*.+$", header)
        if not declared_name or declared_name.group(1) != name or not description:
            raise WorkbenchError(f"Skill frontmatter does not match expected skill {name!r}: {path}")
        sources[name] = content.rstrip() + "\n"
    rule = specs_root / "RULE_MAINTENANCE_SPEC.md"
    if not rule.is_file():
        raise WorkbenchError(f"Required rule-maintenance spec is missing: {rule}")
    sources["rule-maintenance"] = RULE_HEADER + rule.read_text(encoding="utf-8").rstrip() + "\n"
    return sources

def sync_managed_skills(sources: dict[str, str], skill_root: Path, manifest: dict) -> tuple[dict[str, str], list[str]]:
    owned = manifest.get("managed_files", {})
    updates, conflicts, targets = {}, [], []
    for name, content in sources.items():
        target = skill_root / name / "SKILL.md"
        key = str(target)
        targets.append(key)
        if target.is_symlink():
            conflicts.append(f"Refusing to replace symlinked skill: {target}")
            continue
        if target.exists():
            current = sha256_text(target.read_text(encoding="utf-8"))
            if key in owned:
                if current != owned[key]:
                    conflicts.append(f"Modified managed skill: {target}")
            elif current == sha256_text(content):
                continue
            else:
                conflicts.append(f"Unmanaged skill already exists: {target}")
                continue
        updates[key] = content
    if conflicts:
        raise ManagedConflictError("\n".join(conflicts))
    return updates, targets
