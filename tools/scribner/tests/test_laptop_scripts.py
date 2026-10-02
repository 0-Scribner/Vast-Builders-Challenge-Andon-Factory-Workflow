"""Exercise the real push helper against disposable local Git remotes."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class PushBothTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scribner-push-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "work"
        self.repo.mkdir()
        self.git("init", "-b", "primary")
        self.git("config", "user.name", "Scribner test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        (self.repo / "scripts").mkdir()
        source = Path(__file__).resolve().parents[3] / "scripts" / "push_both.sh"
        shutil.copy2(source, self.repo / "scripts" / "push_both.sh")
        self.git("add", "scripts/push_both.sh")
        self.git("commit", "-m", "Fixture")
        for name in ("origin", "github"):
            remote = self.root / (name + ".git")
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            self.git("remote", "add", name, str(remote))

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, stderr=subprocess.PIPE, text=True).strip()

    def push(self):
        return subprocess.run(["bash", "scripts/push_both.sh"], cwd=self.repo, capture_output=True, text=True)

    def test_pushes_both_and_preserves_origin_upstream(self):
        result = self.push()
        self.assertEqual(result.returncode, 0, result.stderr)
        head = self.git("rev-parse", "HEAD")
        for remote in ("origin", "github"):
            self.assertEqual(self.git("ls-remote", remote, "refs/heads/primary").split()[0], head)
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "@{upstream}"), "origin/primary")

    def test_staged_media_and_secrets_refused_before_push(self):
        for name in ("random.mp4", "corpus.zip", ".env", "team.config"):
            with self.subTest(name=name):
                (self.repo / name).write_text("disposable test fixture\n")
                self.git("add", name)
                result = self.push()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("push_both: refuse", result.stderr)
                for remote in ("origin", "github"):
                    self.assertEqual(self.git("ls-remote", remote), "")
                self.git("reset", "--", name)
                (self.repo / name).unlink()

    def test_failed_origin_is_reported_even_if_github_succeeds(self):
        self.git("remote", "set-url", "origin", str(self.root / "missing.git"))
        result = self.push()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("origin push failed", result.stderr)
        self.assertEqual(self.git("ls-remote", "github", "refs/heads/primary").split()[0], self.git("rev-parse", "HEAD"))
