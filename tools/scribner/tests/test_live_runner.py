"""Smoke tests for workshop/00_run_live.sh that need no workshop VM."""

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "workshop" / "00_run_live.sh"
STEPS = ["config", "deps", "02", "03", "app", "health", "05", "06", "09", "stop", "07", "08"]


def find_bash():
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    if os.name == "nt" and git_bash.is_file():
        return str(git_bash)
    found = shutil.which("bash")
    if found and not re.search(r"(?i)system32|windowsapps", found):
        return found
    return None


BASH = find_bash()


@unittest.skipIf(BASH is None, "no bash interpreter")
class LiveRunnerTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            [BASH, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, timeout=60
        )

    def test_syntax(self):
        result = subprocess.run([BASH, "-n", str(SCRIPT)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_dry_run_lists_every_step_in_order(self):
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        planned = re.findall(r"^PLAN (\S+)", result.stdout, re.M)
        self.assertEqual(planned, STEPS)
        self.assertIn("nothing ran", result.stdout)

    def test_unknown_flag_exits_2_and_echoes_it(self):
        result = self.run_script("--bogus-flag")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--bogus-flag", result.stderr)

    def test_no_environment_dumps(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("set -x", text)
        self.assertNotIn("printenv", text)
        self.assertIsNone(re.search(r"^\s*env\s*$", text, re.M))


if __name__ == "__main__":
    unittest.main()
