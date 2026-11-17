import json
import tempfile
import unittest
from pathlib import Path

from ai_workbench.core import ManagedConflictError
from ai_workbench.project import initialize_project

class ProjectTests(unittest.TestCase):
    def test_init_is_idempotent_and_preserves_existing_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            agents.write_text("# Existing project rules\nDo not remove.\n")
            first = initialize_project(root)
            content1 = agents.read_text()
            second = initialize_project(root)
            self.assertEqual(agents.read_text(), content1)
            self.assertTrue(first["agents_updated"])
            self.assertFalse(second["agents_updated"])
            self.assertIn("Do not remove.", content1)
            self.assertTrue((root / ".ai-workbench/PROJECT_STATE.md").exists())
            self.assertTrue((root / ".ai-workbench/managed.json").exists())
            self.assertTrue((root / ".ai-workbench/config.json").exists())

    def test_init_does_not_overwrite_modified_managed_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_project(root)
            agents = root / "AGENTS.md"
            self.assertTrue(agents.exists())
            agents.write_text(agents.read_text().replace("Reuse existing", "Do not reuse"))
            with self.assertRaises(ManagedConflictError):
                initialize_project(root)

    def test_init_does_not_claim_existing_unmanaged_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("<!-- AI-WORKBENCH:START -->\ncustom\n<!-- AI-WORKBENCH:END -->")
            with self.assertRaises(ManagedConflictError):
                initialize_project(root)

    def test_existing_project_state_and_config_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".ai-workbench"
            state_dir.mkdir()
            (state_dir / "PROJECT_STATE.md").write_text("user state\n")
            (state_dir / "config.json").write_text(json.dumps({"custom": True}))
            initialize_project(root)
            self.assertEqual((state_dir / "PROJECT_STATE.md").read_text(), "user state\n")
            self.assertEqual(json.loads((state_dir / "config.json").read_text()), {"custom": True})

if __name__ == "__main__":
    unittest.main()
