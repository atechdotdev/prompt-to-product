"""R1160 test by hand: the plan, the record and the honest status
(agent_kit/p2p_qa.py).

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1160
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
if KIT not in sys.path:
    sys.path.insert(0, KIT)

import p2p_brief as B                                          # noqa: E402
import p2p_qa as Q                                             # noqa: E402

PROMPT = ("A desk buddy for kids with a button that plays a tune, and a light that glows "
          "red when it is too hot.")
FACTS = {"parts": [{"label": "Case", "count": 1}, {"label": "Lid", "count": 1}],
         "modules": ["button", "light", "speaker", "temp_humidity", "usbc"],
         "screws": ["M3 x 8 mm screw"],
         "accept": [{"id": "size", "text": "Fits in 120 x 75 x 30 mm", "state": "unknown",
                     "detail": ""}, {"id": "checked", "text": "Passes ./check",
                                     "state": "met", "detail": ""}]}


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.tests = Q.plan(B.brief(PROMPT), FACTS)
        self.ids = [t["id"] for t in self.tests]

    def test_groups(self):
        groups = {t["group"] for t in self.tests}
        self.assertEqual(groups, set(Q.GROUPS) - set())
        self.assertEqual(len(self.ids), len(set(self.ids)), "ids are unique")

    def test_contents(self):
        self.assertIn("print:case", self.ids)
        self.assertIn("fit:m3-x-8-mm-screw", self.ids)
        self.assertIn("modules:speaker", self.ids)
        self.assertNotIn("modules:usbc", self.ids)
        self.assertTrue(any(i.startswith("behaviour:1-") for i in self.ids))
        self.assertIn("brief:size", self.ids, "a criterion not met by the computer")
        self.assertNotIn("brief:checked", self.ids, "a met one is not asked again")
        self.assertIn("safety:pull", self.ids, "kids: pull test")

    def test_stable_ids(self):
        again = [t["id"] for t in Q.plan(B.brief(PROMPT), FACTS)]
        self.assertEqual(again, self.ids)

    def test_a_print_has_no_power_tests(self):
        ids = [t["id"] for t in Q.plan(B.brief("a vase"), {"parts": [{"label": "Vase"}]})]
        self.assertEqual(ids, ["print:vase", "safety:edges"])


class TestStatus(unittest.TestCase):
    def setUp(self):
        self.tests = Q.plan(B.brief(PROMPT), FACTS)

    def test_not_tested(self):
        st = Q.status(self.tests, {})
        self.assertEqual(st["state"], "not tested")
        self.assertIn("Not tested by hand yet", st["line"])

    def test_partly_failed_and_tested(self):
        rec = Q.result({}, "print:case", Q.PASS)
        self.assertEqual(Q.status(self.tests, rec)["state"], "partly tested")
        rec = Q.result(rec, "print:lid", Q.FAIL, "warped corner")
        st = Q.status(self.tests, rec)
        self.assertEqual(st["state"], "failed")
        self.assertIn("Print Lid", st["line"])
        rec = {}
        for t in self.tests:
            rec = Q.result(rec, t["id"], Q.PASS)
        rec = Q.result(rec, "safety:pull", Q.SKIP)
        st = Q.status(self.tests, rec)
        self.assertEqual(st["state"], "tested")
        self.assertIn("(1 skipped)", st["line"])

    def test_stale_results_do_not_count(self):
        rec = Q.result({}, "print:old-part", Q.PASS)
        self.assertEqual(Q.status(self.tests, rec)["state"], "not tested")

    def test_bad_outcome(self):
        with self.assertRaises(ValueError):
            Q.result({}, "x", "maybe")

    def test_record_file_and_markdown(self):
        d = tempfile.mkdtemp()
        try:
            rec = Q.result({}, "print:case", Q.PASS, "fine")
            Q.save_record(d, rec)
            self.assertEqual(Q.load_record(d)["print:case"]["note"], "fine")
            md = Q.markdown(self.tests, Q.load_record(d))
            self.assertIn("- [x] Print Case.", md)
            self.assertIn("- [ ] Print Lid.", md)
            self.assertIn("### Behaviour", md)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
