from __future__ import annotations
import json, os, shlex, shutil, stat, subprocess, sys
from pathlib import Path
from typing import Callable
from .core import (END_MARKER, START_MARKER, ManagedConflictError, Paths, WorkbenchError, atomic_write, get_paths, managed_block_hash, read_manifest, read_text_exact, replace_managed_block, remove_managed_block, save_manifest, sha256_file, sha256_text)
from .specs import ensure_specs_checkout, load_skill_sources, sync_managed_skills

GLOBAL_BLOCK = f"""{START_MARKER}
# AI Workbench — Codex collaboration contract

For software, architecture, debugging, refactoring, documentation or delivery work, use the installed $ai-workbench skill when relevant. It translates the audit-derived workflow into conditional execution behavior; it does not override project instructions or the latest user request.

- Establish the active goal and latest constraints before acting. New constraints supersede stale plans and stop work that no longer serves the current outcome.
- Inspect the actual repository, worktree, branch, cwd, implementation, runtime and entry points. Do not infer project structure from memory or filenames alone.
- Reuse existing UI, APIs, data models, tools and runtime capabilities before creating parallel implementations.
- Keep confirmed intent, observed implementation, verified outcomes, hypotheses and unknowns distinct.
- Choose the smallest implementation that achieves the requested outcome without weakening confirmed behavior or leaving confirmed business rules disconnected from the real path.
- For multi-step work, use current planning/execution skills when their triggers apply. For behavior-changing production code, follow TDD. Use finding-closure discipline when claiming a confirmed finding is remediated.
- Keep one primary agent accountable for end-to-end completion. Delegate only independent work with clear contracts and integration evidence.
- Verify the final changed state. Report what was tested, which environment and entry point were used, and what remains unverified.
- Maintain concise durable project state for meaningful decisions and recovery; do not turn conversation history into a second source of truth.
- Ask the user only for required access, authority or a material business decision that repository evidence cannot resolve.

Avoid ceremony: do not force plans, broad scans, multiple agents, full-suite tests or extra documentation onto small bounded changes.

Installed source skills: $task-execution-discipline, $executing-plans, $executing-dependent-plans, $test-driven-development, $auditing-finding-closure, $writing-plans, $writing-specs, $rule-maintenance.
{END_MARKER}"""

def _run(args: list[str], cwd: Path | None = None, runner: Callable | None = None):
    if runner:
        return runner(args, cwd=cwd)
    return subprocess.run(args, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)

def _install_block(path: Path, block: str, expected_hash: str | None) -> str:
    current = read_text_exact(path) if path.exists() else ""
    existing_hash = managed_block_hash(current)
    if existing_hash is not None and (expected_hash is None or existing_hash != expected_hash):
        raise ManagedConflictError(f"Managed instructions are not owned by this install or were edited: {path}")
    updated = replace_managed_block(current, block)
    if updated != current:
        atomic_write(path, updated)
    return managed_block_hash(updated) or ""

def _copy_runtime(source_root: Path, paths: Paths) -> dict[str, str]:
    package = source_root / "ai_workbench"
    skill = source_root / "skills" / "ai-workbench" / "SKILL.md"
    entry = source_root / "aiw.py"
    if not package.is_dir() or not skill.is_file() or not entry.is_file():
        raise WorkbenchError(f"Incomplete AI Workbench source tree: {source_root}")
    managed: dict[str, str] = {}
    for source in package.glob("*.py"):
        destination = paths.bin_dir / "ai_workbench" / source.name
        content = source.read_text(encoding="utf-8")
        atomic_write(destination, content)
        managed[str(destination)] = sha256_text(content)
    skill_target = paths.bin_dir / "skills" / "ai-workbench" / "SKILL.md"
    skill_content = skill.read_text(encoding="utf-8")
    atomic_write(skill_target, skill_content)
    managed[str(skill_target)] = sha256_text(skill_content)
    entry_content = entry.read_text(encoding="utf-8")
    atomic_write(paths.installed_script, entry_content)
    managed[str(paths.installed_script)] = sha256_text(entry_content)
    if paths.is_windows:
        shim = f'@echo off\r\n"{Path(sys.executable)}" "%~dp0aiw.py" %*\r\n'
        atomic_write(paths.launcher, shim)
    else:
        shim = '#!/usr/bin/env sh\nexec ' + shlex.quote(sys.executable) + ' "$(dirname "$0")/aiw.py" "$@"\n'
        atomic_write(paths.launcher, shim, mode=0o755)
        os.chmod(paths.launcher, 0o755)
    managed[str(paths.launcher)] = sha256_text(shim)
    return managed

def _preflight_runtime(paths: Paths, source_root: Path, previous: dict) -> list[Path]:
    candidates = [paths.installed_script, paths.launcher]
    candidates += [paths.bin_dir / "ai_workbench" / p.name for p in (source_root / "ai_workbench").glob("*.py")]
    candidates += [paths.bin_dir / "skills" / "ai-workbench" / "SKILL.md"]
    for target in candidates:
        if target.is_symlink():
            raise ManagedConflictError(f"Refusing to replace a symlinked launcher/package target: {target}")
        if not target.exists():
            continue
        expected = previous.get(str(target))
        if expected is None:
            raise ManagedConflictError(f"Unmanaged launcher/package file already exists: {target}")
        if sha256_file(target) != expected:
            raise ManagedConflictError(f"Managed launcher/package file was edited: {target}")
    return candidates

def _snapshot(paths: list[Path]) -> dict[Path, tuple[str | None, int | None]]:
    saved = {}
    for path in paths:
        if path.exists():
            if path.is_symlink():
                raise ManagedConflictError(f"Refusing to replace symlink: {path}")
            saved[path] = (read_text_exact(path), stat.S_IMODE(path.stat().st_mode))
        else:
            saved[path] = (None, None)
    return saved

def _rollback(saved: dict[Path, tuple[str | None, int | None]]) -> list[str]:
    failures = []
    for path, (content, mode) in reversed(list(saved.items())):
        try:
            if content is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, content, mode=mode)
        except Exception as exc:
            failures.append(f"{path}: {exc}")
    return failures

def install(paths: Paths | None = None, specs_dir: Path | None = None, source_root: Path | None = None, runner: Callable | None = None, update_specs: bool | None = None) -> dict:
    paths = paths or get_paths()
    source_root = (source_root or Path(__file__).resolve().parent.parent).resolve()
    manifest = read_manifest(paths.manifest)
    invalid_paths = _invalid_manifest_paths(manifest, paths)
    if invalid_paths:
        raise WorkbenchError("Install manifest contains paths outside AI Workbench-managed directories: " + ", ".join(invalid_paths))
    specs_path = (specs_dir or Path(manifest.get("specs_dir") or paths.specs_dir)).expanduser().resolve()
    should_update = (specs_dir is None) if update_specs is None else update_specs
    info = ensure_specs_checkout(specs_path, runner=runner, update_existing=should_update)
    sources = load_skill_sources(info.root)
    bundled_skill = source_root / "skills" / "ai-workbench" / "SKILL.md"
    if not bundled_skill.is_file():
        raise WorkbenchError(f"Bundled skill is missing: {bundled_skill}")
    sources["ai-workbench"] = bundled_skill.read_text(encoding="utf-8").rstrip() + "\n"
    old_files = manifest.get("managed_files", {})
    if paths.global_agents.is_symlink():
        raise ManagedConflictError(f"Refusing to replace symlinked global instructions: {paths.global_agents}")
    if paths.global_agents.exists():
        old_block = managed_block_hash(read_text_exact(paths.global_agents))
        if old_block is not None and (manifest.get("global_agents_block_hash") is None or old_block != manifest.get("global_agents_block_hash")):
            raise ManagedConflictError(f"Global Codex instructions contain unowned or modified AI Workbench markers: {paths.global_agents}")
    skill_updates, _ = sync_managed_skills(sources, paths.skills_dir, manifest)
    runtime_targets = _preflight_runtime(paths, source_root, old_files)
    global_before = read_text_exact(paths.global_agents) if paths.global_agents.exists() else ""
    had_block = managed_block_hash(global_before) is not None
    separator_added = manifest.get("global_agents_separator_added") if had_block else bool(global_before and not global_before.endswith("\n"))
    affected = [paths.global_agents, paths.manifest] + [Path(item) for item in skill_updates] + runtime_targets
    saved = _snapshot(list(dict.fromkeys(affected)))
    try:
        block_hash = _install_block(paths.global_agents, GLOBAL_BLOCK, manifest.get("global_agents_block_hash"))
        hashes = dict(old_files)
        for target_text, content in skill_updates.items():
            atomic_write(Path(target_text), content)
            hashes[target_text] = sha256_text(content)
        hashes.update(_copy_runtime(source_root, paths))
        manifest.update({"version": 1, "specs_dir": str(info.root), "specs_repository": info.remote, "specs_commit": info.commit, "global_agents_path": str(paths.global_agents), "global_agents_block_hash": block_hash, "global_agents_separator_added": bool(separator_added), "skills_dir": str(paths.skills_dir), "managed_files": hashes, "launcher_path": str(paths.launcher)})
        save_manifest(paths.manifest, manifest)
    except Exception as exc:
        rollback_failures = _rollback(saved)
        if rollback_failures:
            raise WorkbenchError(f"Install failed: {exc}. Rollback also failed: {'; '.join(rollback_failures)}") from exc
        raise
    return {"specs_commit": info.commit, "skills_installed": len(sources), "launcher": str(paths.launcher), "global_agents": str(paths.global_agents)}

def _managed_path_allowed(target: Path, paths: Paths) -> bool:
    if target.is_symlink():
        return False
    resolved = target.resolve(strict=False)
    roots = (paths.bin_dir.resolve(strict=False), paths.skills_dir.resolve(strict=False))
    return any(resolved != root and root in resolved.parents for root in roots)

def _invalid_manifest_paths(manifest: dict, paths: Paths) -> list[str]:
    return [name for name in manifest.get("managed_files", {}) if not _managed_path_allowed(Path(name), paths)]

def _check(label: str, ok: bool, detail: str, warning: bool = False) -> dict:
    return {"label": label, "status": "OK" if ok else ("WARN" if warning else "FAIL"), "detail": detail}

def doctor(paths: Paths | None = None, project_root: Path | None = None) -> list[dict]:
    paths = paths or get_paths()
    checks = [_check("Python", sys.version_info >= (3, 10), sys.version.split()[0] + " (requires 3.10+)"), _check("Git", bool(shutil.which("git")), shutil.which("git") or "git is not on PATH")]
    codex = shutil.which("codex")
    checks.append(_check("Codex CLI", bool(codex), (codex + " (authentication not checked)" if codex else "codex is not on PATH; install and authenticate Codex CLI")))
    manifest = read_manifest(paths.manifest)
    specs = Path(manifest.get("specs_dir") or paths.specs_dir)
    git = shutil.which("git")
    current_commit = None
    if git and specs.is_dir():
        result = _run([git, "rev-parse", "HEAD"], specs)
        if result.returncode == 0:
            current_commit = result.stdout.strip()
    source_ok = bool(current_commit and current_commit == manifest.get("specs_commit"))
    source_detail = f"{specs} @ {current_commit}" if current_commit else f"Not installed/readable: {specs}"
    if current_commit and git:
        branch = _run([git, "branch", "--show-current"], specs)
        dirty = _run([git, "status", "--porcelain"], specs)
        remote = _run([git, "remote", "get-url", "origin"], specs)
        from .specs import REPO_URL, _canonical_remote
        source_ok = source_ok and branch.returncode == 0 and branch.stdout.strip() == "main" and dirty.returncode == 0 and not dirty.stdout.strip() and remote.returncode == 0 and _canonical_remote(remote.stdout) == _canonical_remote(REPO_URL)
    if current_commit and not source_ok:
        source_detail += f" (expected clean main at {manifest.get('specs_commit')}; run aiw update or inspect checkout)"
    checks.append(_check("ai-specs checkout", source_ok, source_detail))
    block = None
    global_error = None
    if paths.global_agents.exists():
        try:
            if not paths.global_agents.is_symlink():
                block = managed_block_hash(read_text_exact(paths.global_agents))
            else:
                global_error = "symlinked file is not managed"
        except WorkbenchError as exc:
            global_error = str(exc)
    global_ok = bool(block and block == manifest.get("global_agents_block_hash"))
    checks.append(_check("Global Codex instructions", global_ok, global_error or str(paths.global_agents)))
    required = ["ai-workbench", "task-execution-discipline", "executing-plans", "executing-dependent-plans", "test-driven-development", "auditing-finding-closure", "writing-plans", "writing-specs", "rule-maintenance"]
    missing = [name for name in required if not (paths.skills_dir / name / "SKILL.md").is_file()]
    checks.append(_check("Installed skills", not missing, "All required skills present" if not missing else "Missing: " + ", ".join(missing)))
    invalid_paths = _invalid_manifest_paths(manifest, paths)
    modified, absent = [], []
    for target_text, expected in manifest.get("managed_files", {}).items():
        target = Path(target_text)
        if target_text in invalid_paths:
            modified.append(target_text + " (outside managed directories)")
        elif not target.exists():
            absent.append(target_text)
        elif sha256_file(target) != expected:
            modified.append(target_text)
    integrity = not modified and not absent
    detail = "Managed files match install manifest" if integrity else "Modified/unsafe: " + ", ".join(modified) + "; missing: " + ", ".join(absent)
    checks.append(_check("Managed file integrity", integrity, detail))
    checks.append(_check("Launcher", paths.launcher.exists() and paths.installed_script.exists(), str(paths.launcher)))
    path_entries = [os.path.normcase(os.path.normpath(item)) for item in os.environ.get("PATH", "").split(os.pathsep) if item]
    on_path = os.path.normcase(os.path.normpath(str(paths.bin_dir))) in path_entries
    checks.append(_check("Launcher PATH", on_path, str(paths.bin_dir) + (" is on PATH" if on_path else " is not on current PATH")))
    if project_root is not None:
        root = project_root.expanduser().resolve()
        agents = root / "AGENTS.md"
        state = root / ".ai-workbench" / "PROJECT_STATE.md"
        owner = root / ".ai-workbench" / "managed.json"
        ok = False
        if agents.exists() and state.exists() and owner.exists():
            try:
                data = json.loads(owner.read_text(encoding="utf-8"))
                ok = managed_block_hash(read_text_exact(agents)) == data.get("project_agents_block_hash")
            except (OSError, ValueError, WorkbenchError):
                ok = False
        checks.append(_check("Project initialized", ok, str(root)))
    return checks

def status(paths: Paths | None = None) -> dict:
    paths = paths or get_paths()
    manifest = read_manifest(paths.manifest)
    return {"installed": paths.manifest.exists(), "specs_repository": manifest.get("specs_repository"), "specs_dir": manifest.get("specs_dir"), "specs_commit": manifest.get("specs_commit"), "launcher": manifest.get("launcher_path"), "managed_files": len(manifest.get("managed_files", {}))}

def launch_codex(project_root: Path, args: list[str] | None = None, runner: Callable | None = None) -> int:
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise WorkbenchError(f"Project directory does not exist: {root}")
    executable = shutil.which("codex")
    if not executable:
        raise WorkbenchError("Codex CLI was not found on PATH. Install it, then run aiw doctor.")
    command = [executable] + list(args or [])
    if runner:
        result = runner(command, cwd=root)
    else:
        # Inherit stdin/stdout/stderr so Codex remains an interactive terminal application.
        result = subprocess.run(command, cwd=str(root), check=False)
    return int(result.returncode)

def uninstall(paths: Paths | None = None) -> dict:
    paths = paths or get_paths()
    manifest = read_manifest(paths.manifest)
    removed, preserved = [], []
    if paths.global_agents.exists():
        if paths.global_agents.is_symlink():
            preserved.append(str(paths.global_agents) + " (symlink; preserved)")
        else:
            text = read_text_exact(paths.global_agents)
            digest = managed_block_hash(text)
            if digest and digest == manifest.get("global_agents_block_hash"):
                atomic_write(paths.global_agents, remove_managed_block(text, bool(manifest.get("global_agents_separator_added"))))
                removed.append(str(paths.global_agents) + " (managed block)")
            elif digest:
                preserved.append(str(paths.global_agents) + " (modified managed block)")
            elif manifest.get("global_agents_block_hash"):
                preserved.append(str(paths.global_agents) + " (managed block missing or markers removed)")
    for name, expected in manifest.get("managed_files", {}).items():
        path = Path(name)
        if not _managed_path_allowed(path, paths):
            preserved.append(str(path) + " (outside managed directories; preserved)")
            continue
        if not path.exists():
            continue
        if path.is_symlink():
            preserved.append(str(path) + " (symlink; preserved)")
            continue
        if sha256_file(path) == expected:
            path.unlink()
            removed.append(str(path))
        else:
            preserved.append(str(path) + " (modified; preserved)")
    for directory in (paths.skills_dir, paths.bin_dir):
        if directory.exists():
            for child in sorted(directory.rglob("*"), reverse=True):
                if child.is_dir():
                    try:
                        child.rmdir()
                    except OSError:
                        pass
    paths.manifest.unlink(missing_ok=True)
    return {"removed": removed, "preserved": preserved, "specs_checkout_preserved": str(paths.specs_dir)}
