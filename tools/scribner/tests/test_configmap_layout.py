"""The static dir must survive the Kubernetes ConfigMap symlink layout.

A code ConfigMap mounted at /code exposes each file as a symlink into a hidden
timestamped directory, and the static ConfigMap is a second mount at /code/static.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIBNER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIBNER))


class ConfigMapLayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="scribner-cm-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_static_dir_is_the_mount_beside_the_symlinked_code(self):
        hidden = self.tmp / "code" / "..2026_10_02_00_00_00.1"
        hidden.mkdir(parents=True)
        shutil.copy2(SCRIBNER / "config.py", hidden / "config.py")
        link = self.tmp / "code" / "config.py"
        try:
            os.symlink(hidden / "config.py", link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks unavailable here: {exc}")
        (self.tmp / "code" / "static").mkdir()
        spec = importlib.util.spec_from_file_location("config_configmap_layout", link)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(Path(module.STATIC_DIR), self.tmp / "code" / "static")
        self.assertTrue(Path(module.STATIC_DIR).is_dir())


if __name__ == "__main__":
    unittest.main()
