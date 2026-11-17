import tempfile
import unittest
from pathlib import Path

from ai_workbench.core import (
    ManagedConflictError, atomic_write, extract_managed_block, get_paths,
    managed_block_hash, replace_managed_block, remove_managed_block, sha256_text,
)

class CoreTests(unittest.TestCase):
    def test_platform_paths(self):
        home = Path("/home/tester")
        linux = get_paths({"HOME": str(home)}, platform="posix", home=home)
        self.assertEqual(linux.data_dir, home / ".local/share/ai-workbench")
        self.assertEqual(linux.launcher, home / ".local/bin/aiw")
        win_home = Path("C:/Users/tester")
        windows = get_paths({"USERPROFILE": str(win_home), "LOCALAPPDATA": "C:/Users/tester/AppData/Local"}, platform="nt", home=win_home)
        self.assertEqual(windows.launcher.name, "aiw.cmd")
        self.assertEqual(windows.skills_dir, win_home / ".agents/skills")

    def test_managed_block_insert_replace_and_remove_preserves_unmanaged_text(self):
        original = "# User rules\nKeep this exactly.\n"
        block1 = "<!-- AI-WORKBENCH:START -->\nfirst\n<!-- AI-WORKBENCH:END -->"
        block2 = "<!-- AI-WORKBENCH:START -->\nsecond\n<!-- AI-WORKBENCH:END -->"
        once = replace_managed_block(original, block1)
        twice = replace_managed_block(once, block1)
        self.assertEqual(once, twice)
        replaced = replace_managed_block(once, block2)
        self.assertIn("Keep this exactly.", replaced)
        self.assertIn("second", replaced)
        self.assertNotIn("first", replaced)
        self.assertEqual(remove_managed_block(replaced), original)

    def test_malformed_or_duplicate_markers_are_rejected(self):
        with self.assertRaises(ManagedConflictError):
            extract_managed_block("<!-- AI-WORKBENCH:START -->\nmissing end")
        with self.assertRaises(ManagedConflictError):
            extract_managed_block("<!-- AI-WORKBENCH:START --><!-- AI-WORKBENCH:START --><!-- AI-WORKBENCH:END -->")

    def test_removing_block_restores_file_without_original_trailing_newline(self):
        original = "# User rules without final newline"
        block = "<!-- AI-WORKBENCH:START -->\nmanaged\n<!-- AI-WORKBENCH:END -->"
        updated = replace_managed_block(original, block)
        self.assertEqual(remove_managed_block(updated, separator_added=True), original)

    def test_hash_detects_edit(self):
        self.assertNotEqual(sha256_text("a"), sha256_text("b"))

    def test_atomic_write_creates_parent_and_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "file.txt"
            atomic_write(path, "first")
            atomic_write(path, "second")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(), "second")
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

if __name__ == "__main__":
    unittest.main()
