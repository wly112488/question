import tempfile
import unittest
from pathlib import Path

from ai_workbench.core import ManagedConflictError, WorkbenchError
from ai_workbench.specs import REPO_URL, SKILL_MAP, ensure_specs_checkout, load_skill_sources, sync_managed_skills

def make_specs(root: Path):
    for name, rel in SKILL_MAP.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: Test skill.\n---\n\n# {name}\n", encoding="utf-8")
    (root / "RULE_MAINTENANCE_SPEC.md").write_text("RULE_MAINTENANCE_SPEC\n\nUse smallest safe change.\n", encoding="utf-8")

class SpecsTests(unittest.TestCase):
    def test_loads_all_current_required_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_specs(root)
            sources = load_skill_sources(root)
            self.assertEqual(set(sources), set(SKILL_MAP) | {"rule-maintenance"})
            self.assertIn("smallest safe change", sources["rule-maintenance"])

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WorkbenchError):
                load_skill_sources(Path(tmp))

    def test_skill_sync_does_not_claim_identical_unmanaged_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "task-execution-discipline" / "SKILL.md"
            target.parent.mkdir()
            target.write_text("same\n")
            manifest = {"managed_files": {}}
            updates, _ = sync_managed_skills({"task-execution-discipline": "same\n"}, root, manifest)
            self.assertEqual(updates, {})
            self.assertEqual(manifest["managed_files"], {})

    def test_skill_sync_rejects_unmanaged_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "writing-plans" / "SKILL.md"
            target.parent.mkdir()
            target.write_text("user skill\n")
            with self.assertRaises(ManagedConflictError):
                sync_managed_skills({"writing-plans": "different\n"}, root, {"managed_files": {}})

    def test_skill_sync_rejects_modified_managed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "writing-plans" / "SKILL.md"
            target.parent.mkdir()
            target.write_text("user edit\n")
            with self.assertRaises(ManagedConflictError):
                sync_managed_skills({"writing-plans": "new source\n"}, root, {"managed_files": {str(target): "old-hash"}})

    def test_specs_checkout_rejects_wrong_remote(self):
        from subprocess import CompletedProcess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / ".git").mkdir()
            def runner(args, cwd=None):
                if args[1:3] == ["branch", "--show-current"]: return CompletedProcess(args, 0, "main\n", "")
                if args[1:3] == ["status", "--porcelain"]: return CompletedProcess(args, 0, "", "")
                if args[1:3] == ["rev-parse", "HEAD"]: return CompletedProcess(args, 0, "abc\n", "")
                if args[1:4] == ["remote", "get-url", "origin"]: return CompletedProcess(args, 0, "https://example.com/other.git\n", "")
                return CompletedProcess(args, 0, "", "")
            with self.assertRaises(WorkbenchError):
                ensure_specs_checkout(root, runner=runner, update_existing=False)

    def test_specs_checkout_rejects_non_main_branch(self):
        from subprocess import CompletedProcess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / ".git").mkdir()
            def runner(args, cwd=None):
                if args[1:3] == ["branch", "--show-current"]: return CompletedProcess(args, 0, "feature\n", "")
                return CompletedProcess(args, 0, "", "")
            with self.assertRaises(WorkbenchError):
                ensure_specs_checkout(root, runner=runner, update_existing=False)

    def test_real_clean_main_checkout_is_validated_with_git(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "specs"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
            make_specs(root)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", REPO_URL], cwd=root, check=True)
            info = ensure_specs_checkout(root, update_existing=False)
            self.assertEqual(info.root, root)
            self.assertTrue(info.commit)
            self.assertEqual(info.remote, REPO_URL)

if __name__ == "__main__":
    unittest.main()
