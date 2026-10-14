
import json
import tempfile
import unittest
from pathlib import Path
from legalrobust.cases import load_cases, validate_cases
from legalrobust.scoring import heuristic_score
from legalrobust.reporting import export_report


class CoreTests(unittest.TestCase):
    def test_example_dataset_validates(self):
        path = Path(__file__).parents[1] / "examples" / "cases.json"
        cases = load_cases(path)
        self.assertGreaterEqual(len(cases), 5)

    def test_duplicate_ids_rejected(self):
        base = {"id": "x", "jurisdiction": "Any", "legal_area": "general",
                "dimension": "base_question", "prompt": "Question"}
        with self.assertRaises(ValueError):
            validate_cases([base, dict(base)])

    def test_heuristic_flags_empty_answer(self):
        case = {"dimension": "missing_information", "reference_answer": None,
                "requires_human_review": True}
        score = heuristic_score(case, "")
        self.assertEqual(score["heuristic_score"], 33.33)
        self.assertIn("empty_response", score["flags"])

    def test_export_creates_three_reports(self):
        report = {"metadata": {"target_model": "fake", "case_count": 0,
                               "completed_count": 0, "failed_count": 0},
                  "summary": {"mean_heuristic_score": None, "dimension_means": {},
                              "human_review_count": 0}, "records": []}
        with tempfile.TemporaryDirectory() as temp:
            export_report(report, temp)
            self.assertTrue((Path(temp) / "report.json").exists())
            self.assertTrue((Path(temp) / "cases.csv").exists())
            self.assertTrue((Path(temp) / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
