import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workbench.commands import doctor, install, launch_codex, status, uninstall
from ai_workbench.core import Paths
from ai_workbench.project import initialize_project
from test_cli import FakeGit, make_source, make_specs

class SmokeTests(unittest.TestCase):
    def test_install_init_doctor_launch_update_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, data, bin_dir = root / "home", root / "data", root / "bin"
            paths = Paths(home, data, data / "ai-specs", home / ".codex", home / ".codex/AGENTS.md", home / ".agents/skills", bin_dir, data / "install-manifest.json", bin_dir / "aiw.py", bin_dir / "aiw", False)
            specs, source, project = root / "specs", root / "source", root / "project"
            project.mkdir()
            make_specs(specs); make_source(source)
            install(paths, specs, source, FakeGit(), update_specs=False)
            initialize_project(project)
            checks = doctor(paths, project)
            self.assertTrue(any(c["label"] == "Project initialized" and c["status"] == "OK" for c in checks))
            self.assertEqual(status(paths)["specs_commit"], "abc123")
            calls = []
            def runner(args, cwd=None):
                from subprocess import CompletedProcess
                calls.append((args, cwd))
                return CompletedProcess(args, 0)
            with patch("ai_workbench.commands.shutil.which", return_value="codex"):
                self.assertEqual(launch_codex(project, ["--help"], runner), 0)
            self.assertEqual(calls[0][0], ["codex", "--help"])
            install(paths, specs, source, FakeGit(), update_specs=False)
            result = uninstall(paths)
            self.assertFalse(paths.launcher.exists())
            self.assertTrue(project.joinpath("AGENTS.md").exists())
            self.assertTrue(specs.exists())
            self.assertEqual(result["preserved"], [])

if __name__ == "__main__":
    unittest.main()
