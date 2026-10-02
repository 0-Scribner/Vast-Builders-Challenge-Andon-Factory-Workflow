"""VSS username resolution must not pick up the Windows login."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402


class VssUsernameTests(unittest.TestCase):
    def test_explicit_vss_username_wins_everywhere(self):
        env = {"VSS_USERNAME": "team-7", "USERNAME": "laptop-login"}
        self.assertEqual(config._vss_username(env, "nt"), "team-7")
        self.assertEqual(config._vss_username(env, "posix"), "team-7")

    def test_windows_ignores_os_username(self):
        self.assertEqual(config._vss_username({"USERNAME": "laptop-login"}, "nt"), "")

    def test_linux_team_config_username_is_used(self):
        self.assertEqual(config._vss_username({"USERNAME": "team-7"}, "posix"), "team-7")

    def test_nothing_set_is_empty(self):
        self.assertEqual(config._vss_username({}, "posix"), "")
        self.assertEqual(config._vss_username({}, "nt"), "")


if __name__ == "__main__":
    unittest.main()
