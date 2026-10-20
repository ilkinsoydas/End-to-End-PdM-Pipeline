import json
from pathlib import Path

from .config import OUTPUT_DIR
from .discover_flights import FlightSegment


def save_split_folds(flights: list[FlightSegment]) -> Path:
    dev_units = sorted({flight.unit for flight in flights})
    folds = []

    for fold_number, validation_unit in enumerate(dev_units, start=1):
        train_units = [unit for unit in dev_units if unit != validation_unit]
        folds.append(
            {
                "fold": fold_number,
                "train_units": train_units,
                "validation_units": [validation_unit],
            }
        )

    split_config = {
        "strategy": "leave_one_engine_out",
        "dev_units": dev_units,
        "official_test_units": [11, 14, 15],
        "folds": folds,
    }
    output_path = OUTPUT_DIR / "split_folds.json"

    with output_path.open(mode="w", encoding="utf-8") as json_file:
        json.dump(split_config, json_file, indent=2, ensure_ascii=False)

    return output_path
