from __future__ import annotations
import hashlib, json, os, stat, tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

START_MARKER = "<!-- AI-WORKBENCH:START -->"
END_MARKER = "<!-- AI-WORKBENCH:END -->"
MANIFEST_VERSION = 1

class WorkbenchError(RuntimeError):
    """A failure that can be resolved by the CLI user."""

class ManagedConflictError(WorkbenchError):
    """Refuse to overwrite content not safely owned by AI Workbench."""

@dataclass(frozen=True)
class Paths:
    home: Path
    data_dir: Path
    specs_dir: Path
    codex_dir: Path
    global_agents: Path
    skills_dir: Path
    bin_dir: Path
    manifest: Path
    installed_script: Path
    launcher: Path
    is_windows: bool

def get_paths(env: Mapping[str, str] | None = None, platform: str | None = None, home: Path | None = None) -> Paths:
    env = dict(os.environ if env is None else env)
    windows = (platform or os.name).lower() in {"nt", "windows", "win32"}
    user_home = Path(home or env.get("USERPROFILE" if windows else "HOME", str(Path.home()))).expanduser()
    if windows:
        local = Path(env.get("LOCALAPPDATA", str(user_home / "AppData" / "Local")))
        data, binary, launcher = local / "AIWorkbench", local / "Programs" / "AIWorkbench", local / "Programs" / "AIWorkbench" / "aiw.cmd"
    else:
        data = Path(env.get("XDG_DATA_HOME", str(user_home / ".local" / "share"))) / "ai-workbench"
        binary, launcher = user_home / ".local" / "bin", user_home / ".local" / "bin" / "aiw"
    codex = user_home / ".codex"
    return Paths(user_home, data, data / "ai-specs", codex, codex / "AGENTS.md", user_home / ".agents" / "skills", binary, data / "install-manifest.json", binary / "aiw.py", launcher, windows)

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_text_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()

def read_manifest(path: Path) -> dict:
    if not path.exists():
        return {"version": MANIFEST_VERSION, "managed_files": {}, "global_agents_block_hash": None}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchError(f"Invalid AI Workbench manifest {path}: {exc}") from exc
    if value.get("version") != MANIFEST_VERSION or not isinstance(value.get("managed_files"), dict):
        raise WorkbenchError(f"Unsupported AI Workbench manifest: {path}")
    return value

def atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None and path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temp, mode)
        os.replace(temp, path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise

def extract_managed_block(content: str, start: str = START_MARKER, end: str = END_MARKER) -> str | None:
    starts, ends = content.count(start), content.count(end)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ManagedConflictError("AI Workbench markers are duplicated or incomplete; file left unchanged.")
    begin, finish = content.index(start), content.index(end)
    if finish < begin:
        raise ManagedConflictError("AI Workbench markers are out of order; file left unchanged.")
    return content[begin:finish + len(end)]

def replace_managed_block(content: str, block: str, start: str = START_MARKER, end: str = END_MARKER) -> str:
    if start not in block or end not in block:
        raise ValueError("Managed replacement must contain both boundary markers.")
    if extract_managed_block(content, start, end) is None:
        prefix = content + ("\n" if content and not content.endswith("\n") else "")
        return prefix + block.rstrip() + "\n"
    begin = content.index(start)
    finish = content.index(end, begin) + len(end)
    return content[:begin] + block.rstrip() + content[finish:]

def remove_managed_block(content: str, separator_added: bool = False, start: str = START_MARKER, end: str = END_MARKER) -> str:
    if extract_managed_block(content, start, end) is None:
        return content
    begin = content.index(start)
    finish = content.index(end, begin) + len(end)
    prefix, suffix = content[:begin], content[finish:]
    if suffix.startswith("\n"):
        suffix = suffix[1:]
    if separator_added and not suffix and prefix.endswith("\n"):
        prefix = prefix[:-1]
    return prefix + suffix

def managed_block_hash(content: str) -> str | None:
    block = extract_managed_block(content)
    return sha256_text(block) if block is not None else None

def save_manifest(path: Path, manifest: dict) -> None:
    atomic_write(path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
