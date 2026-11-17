from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
from . import __version__
from .commands import doctor, install, launch_codex, status, uninstall
from .core import WorkbenchError, get_paths
from .project import initialize_project

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiw", description="AI Workbench for Codex CLI")
    parser.add_argument("--version", action="version", version=f"aiw {__version__}")
    commands = parser.add_subparsers(dest="command")
    p = commands.add_parser("install", help="Install current ai-specs skills and managed Codex instructions")
    p.add_argument("--specs-dir", type=Path, help="Use an existing local ai-specs Git checkout")
    p = commands.add_parser("update", help="Fast-forward ai-specs and refresh managed files")
    p.add_argument("--specs-dir", type=Path, help="Use an existing local ai-specs Git checkout")
    commands.add_parser("doctor", help="Run read-only installation and environment checks")
    commands.add_parser("status", help="Show installed revision and managed file count")
    p = commands.add_parser("init", help="Initialize a project safely")
    p.add_argument("project", nargs="?", default=".", type=Path)
    p = commands.add_parser("launch", help="Launch Codex in a project directory")
    p.add_argument("project", nargs="?", default=".", type=Path)
    commands.add_parser("uninstall", help="Remove unchanged AI Workbench-managed files only")
    return parser

def _checks(checks: list[dict]) -> int:
    width = max((len(item["label"]) for item in checks), default=0)
    for item in checks:
        print(f"{item['status']:<4} {item['label']:<{width}}  {item['detail']}")
    return 1 if any(item["status"] == "FAIL" for item in checks) else 0

def main(argv: list[str] | None = None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    if not args_in:
        try:
            return launch_codex(Path.cwd())
        except WorkbenchError as exc:
            print(f"aiw: {exc}", file=sys.stderr)
            return 2
    codex_args: list[str] = []
    if args_in[0] == "launch" and "--" in args_in:
        separator = args_in.index("--")
        codex_args = args_in[separator + 1:]
        args_in = args_in[:separator]
    parser = _parser()
    args = parser.parse_args(args_in)
    paths = get_paths()
    try:
        if args.command == "install":
            result = install(paths, specs_dir=args.specs_dir)
            print("AI Workbench installed.")
            print(f"ai-specs: {result['specs_commit']}")
            print(f"Skills: {result['skills_installed']}")
            print(f"Launcher: {result['launcher']}")
            if str(paths.bin_dir) not in os.environ.get("PATH", "").split(os.pathsep):
                if paths.is_windows:
                    print("Add this directory to your user PATH, then open a new PowerShell window:")
                    print(f'  $p = [Environment]::GetEnvironmentVariable("Path", "User"); if (($p -split ";") -notcontains "{paths.bin_dir}") {{ [Environment]::SetEnvironmentVariable("Path", (($p.TrimEnd(";") + ";{paths.bin_dir}").Trim(";")), "User") }}')
                else:
                    print("Add this to your shell profile, then open a new terminal:")
                    print('  export PATH="$HOME/.local/bin:$PATH"')
            print("Run aiw doctor, then aiw init <project> in each project.")
            return 0
        if args.command == "update":
            installed = status(paths)
            source = args.specs_dir or Path(installed.get("specs_dir") or paths.specs_dir)
            result = install(paths, specs_dir=source, update_specs=True)
            print(f"Updated from ai-specs {result['specs_commit']}.")
            return 0
        if args.command == "doctor":
            return _checks(doctor(paths, Path.cwd()))
        if args.command == "status":
            print(json.dumps(status(paths), indent=2, ensure_ascii=False))
            return 0
        if args.command == "init":
            result = initialize_project(args.project)
            print(f"Initialized {result['project']}")
            print("Updated project AGENTS.md." if result["agents_updated"] else "Project AGENTS.md already current.")
            print("Created: " + (", ".join(result["created"]) if result["created"] else "no new files"))
            return 0
        if args.command == "launch":
            return launch_codex(args.project, codex_args)
        if args.command == "uninstall":
            result = uninstall(paths)
            print("AI Workbench managed files removed where unchanged.")
            for item in result["removed"]:
                print(f"REMOVED {item}")
            for item in result["preserved"]:
                print(f"PRESERVED {item}")
            print(f"Specs checkout preserved: {result['specs_checkout_preserved']}")
            return 0
        parser.print_help()
        return 0
    except (WorkbenchError, ValueError, OSError) as exc:
        print(f"aiw: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
