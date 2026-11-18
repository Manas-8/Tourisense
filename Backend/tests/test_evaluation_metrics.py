import unittest

from ml_services.train_models import _regression_metrics


class EvaluationMetricTests(unittest.TestCase):
    def test_regression_evaluation_reports_complete_metrics(self):
        metrics = _regression_metrics([1, 2, 3], [1, 3, 2])
        self.assertEqual(0.667, metrics["mae"])
        self.assertEqual(0.667, metrics["mse"])
        self.assertEqual(0.816, metrics["rmse"])
        self.assertIn("r2", metrics)


if __name__ == "__main__":
    unittest.main()
