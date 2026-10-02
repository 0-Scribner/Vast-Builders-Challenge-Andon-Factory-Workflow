"""Explore pages from live VSS builds that name the collection differently."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vss_client import VssClient, VssError  # noqa: E402


class ExploreShapeTests(unittest.TestCase):
    def test_documented_keys_still_work(self):
        batch, total = VssClient._explore_batch({"items": [{"original_video": "a"}], "total": 1})
        self.assertEqual((len(batch), total), (1, 1))

    def test_single_unnamed_collection_is_accepted(self):
        page = {"parents": [{"original_video": "s3://c/a.mp4", "timeline": []}], "total": 1, "scope": "all"}
        batch, total = VssClient._explore_batch(page)
        self.assertEqual(batch[0]["original_video"], "s3://c/a.mp4")
        self.assertEqual(total, 1)

    def test_video_collection_wins_over_other_lists(self):
        page = {"chunks": [{"filename": "a.mp4"}], "warnings": [], "facets": [{"label": "x"}]}
        batch, _ = VssClient._explore_batch(page)
        self.assertEqual(batch, [{"filename": "a.mp4"}])

    def test_ambiguous_page_fails_with_key_names_only(self):
        page = {"a": [{"x": 1}], "b": [{"y": 2}], "token": "secret-value"}
        with self.assertRaises(VssError) as cm:
            VssClient._explore_batch(page)
        self.assertIn("a, b, token", str(cm.exception))
        self.assertNotIn("secret-value", str(cm.exception))

    def test_no_collection_fails(self):
        with self.assertRaises(VssError):
            VssClient._explore_batch({"total": 0})


if __name__ == "__main__":
    unittest.main()
