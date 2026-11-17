import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workbench.commands import doctor, install, launch_codex, status, uninstall
from ai_workbench.core import Paths, ManagedConflictError
from ai_workbench.specs import REPO_URL, SKILL_MAP
from ai_workbench.project import initialize_project

def make_specs(root: Path):
    (root / ".git").mkdir(parents=True, exist_ok=True)
    for name, rel in SKILL_MAP.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: test\n---\n\n# {name}\n", encoding="utf-8")
    (root / "RULE_MAINTENANCE_SPEC.md").write_text("RULE_MAINTENANCE_SPEC\n\nPreserve behavior.\n", encoding="utf-8")

def make_source(root: Path):
    (root / "ai_workbench").mkdir(parents=True, exist_ok=True)
    (root / "ai_workbench/__init__.py").write_text('__version__ = "0.1.0"\n')
    (root / "ai_workbench/cli.py").write_text("def main(): return 0\n")
    (root / "aiw.py").write_text("print('aiw')\n")
    skill = root / "skills/ai-workbench/SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("---\nname: ai-workbench\ndescription: test\n---\n\n# Workbench\n")

class FakeGit:
    def __call__(self, args, cwd=None):
        from subprocess import CompletedProcess
        if args[:2] == ["git", "--version"]:
            return CompletedProcess(args, 0, "git version test", "")
        if args[1:3] == ["status", "--porcelain"]:
            return CompletedProcess(args, 0, "", "")
        if args[1:3] == ["pull", "--ff-only"]:
            return CompletedProcess(args, 0, "Already up to date.", "")
        if args[1:3] == ["rev-parse", "HEAD"]:
            return CompletedProcess(args, 0, "abc123\n", "")
        if args[1:4] == ["remote", "get-url", "origin"]:
            return CompletedProcess(args, 0, REPO_URL + "\n", "")
        if args[1:3] == ["branch", "--show-current"]:
            return CompletedProcess(args, 0, "main\n", "")
        return CompletedProcess(args, 1, "", "unexpected git command")

class CommandTests(unittest.TestCase):
    def make_paths(self, root: Path) -> Paths:
        home = root / "home"
        data = root / "data"
        bin_dir = root / "bin"
        return Paths(home, data, data / "ai-specs", home / ".codex", home / ".codex/AGENTS.md", home / ".agents/skills", bin_dir, data / "install-manifest.json", bin_dir / "aiw.py", bin_dir / "aiw", False)

    def test_install_update_status_and_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            specs = root / "specs"; make_specs(specs)
            source = root / "source"; make_source(source)
            paths.global_agents.parent.mkdir(parents=True)
            paths.global_agents.write_text("# Existing global rules\nKeep me.\n")
            result = install(paths, specs, source, FakeGit(), update_specs=False)
            self.assertEqual(result["specs_commit"], "abc123")
            self.assertIn("Keep me.", paths.global_agents.read_text())
            self.assertTrue((paths.skills_dir / "ai-workbench/SKILL.md").exists())
            self.assertTrue(paths.launcher.exists())
            self.assertEqual(status(paths)["specs_commit"], "abc123")
            install(paths, specs, source, FakeGit(), update_specs=False)
            removed = uninstall(paths)
            self.assertTrue(any("AGENTS.md (managed block)" in item for item in removed["removed"]))
            self.assertFalse(paths.launcher.exists())
            self.assertIn("Keep me.", paths.global_agents.read_text())
            self.assertTrue(specs.exists(), "the source-of-truth checkout is intentionally retained")

    def test_install_refuses_modified_managed_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            specs = root / "specs"; make_specs(specs)
            source = root / "source"; make_source(source)
            install(paths, specs, source, FakeGit(), update_specs=False)
            skill = paths.skills_dir / "writing-plans/SKILL.md"
            self.assertTrue(skill.exists())
            skill.write_text("user modified\n")
            with self.assertRaises(ManagedConflictError):
                install(paths, specs, source, FakeGit(), update_specs=False)

    def test_uninstall_preserves_modified_managed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            specs = root / "specs"; make_specs(specs)
            source = root / "source"; make_source(source)
            install(paths, specs, source, FakeGit(), update_specs=False)
            launcher = paths.launcher
            self.assertTrue(launcher.exists())
            launcher.write_text("user launcher\n")
            result = uninstall(paths)
            self.assertTrue(launcher.exists())
            self.assertTrue(any("modified" in item for item in result["preserved"]))

    def test_launch_forwards_cwd_and_arguments_without_extra_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); calls = []
            def runner(args, cwd=None):
                from subprocess import CompletedProcess
                calls.append((args, cwd))
                return CompletedProcess(args, 0)
            with patch("ai_workbench.commands.shutil.which", return_value="/usr/bin/codex"):
                code = launch_codex(root, ["--model", "test"], runner)
            self.assertEqual(code, 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], ["/usr/bin/codex", "--model", "test"])
            self.assertEqual(calls[0][1], root.resolve())
            self.assertFalse(any("dangerously" in item or "full-auto" in item for item in calls[0][0]))

    def test_doctor_reports_missing_codex_as_failure_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            before = list(root.rglob("*"))
            with patch("ai_workbench.commands.shutil.which", side_effect=lambda name: "/usr/bin/git" if name == "git" else None):
                checks = doctor(paths)
            after = list(root.rglob("*"))
            self.assertEqual(before, after)
            self.assertTrue(any(c["label"] == "Codex CLI" and c["status"] == "FAIL" for c in checks))

    def test_project_init_is_available_from_command_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = initialize_project(Path(tmp))
            self.assertTrue(result["agents_updated"])

    def test_install_rolls_back_partial_writes(self):
        import ai_workbench.commands as commands
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            specs = root / "specs"; make_specs(specs)
            source = root / "source"; make_source(source)
            paths.global_agents.parent.mkdir(parents=True)
            original = "# Keep existing global rules\n"
            paths.global_agents.write_text(original)
            real_write = commands.atomic_write
            count = {"value": 0}
            def fail_once(path, content, mode=None):
                count["value"] += 1
                if count["value"] == 3:
                    raise OSError("simulated disk failure")
                return real_write(path, content, mode)
            with patch("ai_workbench.commands.atomic_write", side_effect=fail_once):
                with self.assertRaises(OSError):
                    install(paths, specs, source, FakeGit(), update_specs=False)
            self.assertEqual(paths.global_agents.read_text(), original)
            self.assertFalse(paths.manifest.exists())
            self.assertFalse((paths.skills_dir / "task-execution-discipline/SKILL.md").exists())

    def test_real_launch_inherits_interactive_terminal_streams(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("ai_workbench.commands.shutil.which", return_value="/usr/bin/codex"), patch("ai_workbench.commands.subprocess.run") as run:
                run.return_value.returncode = 0
                self.assertEqual(launch_codex(Path(tmp)), 0)
                kwargs = run.call_args.kwargs
                self.assertNotIn("capture_output", kwargs)
                self.assertNotIn("stdout", kwargs)
                self.assertNotIn("stdin", kwargs)

    def test_uninstall_refuses_manifest_paths_outside_managed_roots(self):
        from ai_workbench.core import save_manifest, sha256_text
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paths = self.make_paths(root)
            victim = root / "important.txt"; victim.write_text("keep me")
            save_manifest(paths.manifest, {"version": 1, "managed_files": {str(victim): sha256_text("keep me")}})
            result = uninstall(paths)
            self.assertTrue(victim.exists())
            self.assertTrue(any("outside" in item for item in result["preserved"]))

if __name__ == "__main__":
    unittest.main()
