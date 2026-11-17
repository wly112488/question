import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workbench.commands import install, uninstall
from ai_workbench.core import get_paths
from ai_workbench.project import initialize_project
from ai_workbench.specs import REPO_URL, SKILL_MAP


@unittest.skipIf(os.name == "nt", "The live shell-shim smoke test runs on POSIX; Windows launcher paths are covered by unit tests and CI.")
class RealIntegrationTests(unittest.TestCase):
    def _make_specs_checkout(self, root: Path) -> None:
        root.mkdir(parents=True)
        for name, relative in SKILL_MAP.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"---\nname: {name}\ndescription: integration fixture\n---\n\n# {name}\n", encoding="utf-8")
        (root / "RULE_MAINTENANCE_SPEC.md").write_text("# Rule maintenance fixture\n", encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "AIW integration"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", REPO_URL], cwd=root, check=True)

    def test_real_git_install_project_init_launcher_doctor_and_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, data, fakebin = root / "home", root / "data", root / "fakebin"
            project, specs = root / "project", root / "ai-specs"
            for directory in (home, fakebin, project):
                directory.mkdir(parents=True, exist_ok=True)
            self._make_specs_checkout(specs)
            codex = fakebin / "codex"
            codex.write_text('#!/usr/bin/env sh\necho AIW_FAKE_CODEX_OK\nprintf "%s\\n" "$@"\n', encoding="utf-8")
            codex.chmod(0o755)
            env = dict(os.environ)
            env.update({"HOME": str(home), "XDG_DATA_HOME": str(data), "PATH": str(fakebin) + os.pathsep + env.get("PATH", "")})
            paths = get_paths(env=env, platform="posix", home=home)
            source_root = Path(__file__).resolve().parent.parent
            install(paths, specs, source_root, update_specs=False)
            initialize_project(project)
            env["PATH"] = str(paths.bin_dir) + os.pathsep + env["PATH"]
            with patch.dict(os.environ, env, clear=True):
                launched = subprocess.run([str(paths.launcher)], cwd=project, text=True, capture_output=True, check=False)
                self.assertEqual(launched.returncode, 0)
                self.assertIn("AIW_FAKE_CODEX_OK", launched.stdout)
                checked = subprocess.run([sys.executable, str(paths.installed_script), "doctor"], cwd=project, env=env, text=True, capture_output=True, check=False)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                self.assertIn("OK   Project initialized", checked.stdout)
            removed = uninstall(paths)
            self.assertEqual(removed["preserved"], [])
            self.assertFalse(paths.launcher.exists())
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue(specs.exists())


if __name__ == "__main__":
    unittest.main()
