"""The shipped addon carries no personal path or e-mail.

verify_tree.py's "personal data" row scans the built bundle with this same
pattern and fails the build; this test fails first, without a build
(12 Nov 2026: example paths like /Users/a/ in a comment stopped a build).
Write examples as /Users/<you>/ or ~/.

    python -m unittest test_no_personal_paths
"""
import os
import re
import unittest

ADDON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: verify_tree.py's _pii_re (keep the two the same)
PII = re.compile(rb"/home/(?!runner/)[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/"
                 rb"|/tmp/claude-|@gmail\.com")
SKIP_DIRS = {"tests", "__pycache__"}


class TestNoPersonalPaths(unittest.TestCase):
    def test_pattern_matches_verify_tree(self):
        gate = os.path.join(os.path.dirname(os.path.dirname(ADDON)), "branding", "verify_tree.py")
        if not os.path.isfile(gate):
            self.skipTest("no branding/verify_tree.py next to the addon")
        with open(gate, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('/Users/[A-Za-z0-9._-]+/', src)
        self.assertIn('/home/(?!runner/)[A-Za-z0-9._-]+/', src)

    def test_addon_files(self):
        hits = []
        for d, dirs, files in os.walk(ADDON):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            for f in files:
                if f.endswith((".pyc", ".DS_Store")):
                    continue
                p = os.path.join(d, f)
                with open(p, "rb") as fh:
                    m = PII.search(fh.read())
                if m:
                    hits.append("%s: %r" % (os.path.relpath(p, ADDON), m.group(0)))
        self.assertEqual(hits, [], "personal paths would fail the build gate")


if __name__ == "__main__":
    unittest.main()
