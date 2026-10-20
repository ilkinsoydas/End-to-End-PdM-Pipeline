import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import OUTPUT_DIR, STRIDE, WINDOW_SIZE
from .discover_flights import FlightSegment


@dataclass(frozen=True)
class WindowRecord:
    window_id: int
    unit: int
    cycle: int
    rul: float
    start_row: int
    end_row: int


def build_window_records(flights: list[FlightSegment]) -> list[WindowRecord]:
    windows: list[WindowRecord] = []
    window_id = 0

    for flight in flights:
        last_start = flight.end_row - WINDOW_SIZE

        for start_row in range(flight.start_row, last_start + 1, STRIDE):
            windows.append(
                WindowRecord(
                    window_id=window_id,
                    unit=flight.unit,
                    cycle=flight.cycle,
                    rul=flight.rul,
                    start_row=start_row,
                    end_row=start_row + WINDOW_SIZE,
                )
            )
            window_id += 1

    return windows


def save_window_metadata(windows: list[WindowRecord]) -> Path:
    output_path = OUTPUT_DIR / "window_metadata.csv"
    field_names = [
        "window_id",
        "unit",
        "cycle",
        "rul",
        "start_row",
        "end_row",
    ]

    with output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(asdict(window) for window in windows)

    return output_path
