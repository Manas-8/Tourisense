"""Print a fresh evaluation of the experimental trip-cost model, without saving it.

Run from Backend: ``python -m ml_services.evaluate_models`` or
``python -m ml_services.evaluate_models trip-cost``.
"""
import argparse

from ml_services.train_models import _trip_cost_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fresh terminal-only trip-cost regression evaluation")
    parser.add_argument("model", nargs="?", choices=["all", "trip-cost"], default="trip-cost",
                        help="the remaining offline model evaluation")
    parser.parse_args(argv)
    try:
        report = _trip_cost_report(save_artifact=False)
    except Exception as exc:
        print(f"\n=== trip-cost evaluation unavailable ===\nReason: {type(exc).__name__}: {exc}")
        return 1

    print("\n=== Trip-cost Random Forest evaluation ===")
    print(f"Dataset: {report['source']}\nTarget: {report['target']}\nSplit: {report['split']}")
    print(f"Samples: train={report['train_rows']} test={report['test_rows']}")
    for label in ("baseline", "model"):
        metrics = report[label]
        print(f"{label.title()} ({metrics['name']}): "
              f"MAE={metrics['mae']} MSE={metrics['mse']} "
              f"RMSE={metrics['rmse']} R-squared={metrics['r2']}")
    print(f"Limitation: {report['limitation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
