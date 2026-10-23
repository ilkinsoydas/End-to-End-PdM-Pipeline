"""Analyze saved CNN predictions without retraining the model."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--predictions", default="validation_predictions.csv")
    args = parser.parse_args()
    data = pd.read_csv(args.run_dir / args.predictions)
    required = ["unit", "cycle", "true_rul", "predicted_rul"]
    if data.empty or data[required].isna().any().any():
        raise ValueError("Missing or empty prediction data")
    if not np.isfinite(data[required].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite values in predictions")
    if data.groupby(["unit", "cycle"])["true_rul"].nunique().gt(1).any():
        raise ValueError("RUL labels differ within a flight")
    out = args.run_dir / "analysis"
    out.mkdir(exist_ok=True)
    data["error"] = data.predicted_rul - data.true_rul
    flights = data.groupby(["unit", "cycle"], as_index=False).agg(
        true_rul=("true_rul", "first"),
        predicted_rul=("predicted_rul", "mean"),
        window_count=("predicted_rul", "size"),
        prediction_std=("predicted_rul", "std"),
    )
    flights["error"] = flights.predicted_rul - flights.true_rul
    flights.to_csv(out / "flight_predictions.csv", index=False)
    rows = []
    for level, frame in [("window", data), ("flight_mean", flights)]:
        for unit, group in frame.groupby("unit"):
            error = group.error.to_numpy()
            rows.append(dict(level=level, unit=unit, count=len(group),
                             mae=np.abs(error).mean(),
                             rmse=np.sqrt(np.mean(error**2)), bias=error.mean()))
    metrics = pd.DataFrame(rows)
    metrics.to_csv(out / "metrics_by_level.csv", index=False)
    data["rul_range"] = pd.cut(data.true_rul, [-np.inf, 10, 25, 50, np.inf],
                               labels=["<=10", "11-25", "26-50", ">50"])
    bins = []
    for (unit, interval), group in data.groupby(["unit", "rul_range"], observed=True):
        error = group.error.to_numpy()
        bins.append(dict(unit=unit, rul_range=str(interval), count=len(group),
                         mae=np.abs(error).mean(),
                         rmse=np.sqrt(np.mean(error**2)), bias=error.mean()))
    pd.DataFrame(bins).to_csv(out / "rul_range_metrics.csv", index=False)
    for unit, group in flights.groupby("unit"):
        group = group.sort_values("cycle")
        windows = data[data.unit == unit]
        fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
        axes[0].scatter(windows.cycle, windows.predicted_rul, s=8,
                        alpha=.18, label="Window predictions")
        axes[0].plot(group.cycle, group.true_rul, color="black", label="True RUL")
        axes[0].plot(group.cycle, group.predicted_rul, color="tab:orange",
                     label="Mean prediction per flight")
        axes[0].set(ylabel="RUL (cycles)", title=f"Validation motor {unit}")
        axes[0].legend()
        axes[1].plot(group.cycle, group.error, color="tab:red")
        axes[1].axhline(0, color="black", linestyle="--")
        axes[1].set(xlabel="Flight / cycle", ylabel="Predicted - true RUL")
        for ax in axes:
            ax.grid(alpha=.25)
        fig.tight_layout()
        fig.savefig(out / f"rul_by_flight_unit_{unit}.png", dpi=180)
        plt.close(fig)
    print(metrics.to_string(index=False))
    print(f"Analysis saved: {out}")


if __name__ == "__main__":
    main()
