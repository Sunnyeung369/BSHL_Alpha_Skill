from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bshl.files import write_text


class AtomicArtifactTests(unittest.TestCase):
    def test_competing_writers_never_overwrite_a_complete_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "result.txt"
            def attempt(content):
                try:
                    write_text(content, target)
                    return "written"
                except FileExistsError:
                    return "preserved"
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(attempt, ("first" * 1000, "second" * 1000)))
            self.assertEqual(sorted(results), ["preserved", "written"])
            self.assertIn(target.read_text(), ("first" * 1000, "second" * 1000))
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_failed_publish_leaves_no_partial_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "result.txt"
            with patch("bshl.files.os.link", side_effect=OSError("test interruption")):
                with self.assertRaises(OSError):
                    write_text("complete content", target)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])
