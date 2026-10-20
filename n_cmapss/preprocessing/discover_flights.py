from dataclasses import dataclass

import h5py
import numpy as np

from .config import DATA_PATH


@dataclass(frozen=True)
class FlightSegment:
    unit: int
    cycle: int
    start_row: int
    end_row: int
    rul: float

    @property
    def row_count(self) -> int:
        return self.end_row - self.start_row


def discover_flights() -> list[FlightSegment]:
    with h5py.File(DATA_PATH, mode="r") as h5_file:
        identifiers = h5_file["A_dev"][:, :2].astype(np.int32)
        units = identifiers[:, 0]
        cycles = identifiers[:, 1]

        flight_changed = (
            (units[1:] != units[:-1]) | (cycles[1:] != cycles[:-1])
        )
        start_rows = np.concatenate(([0], np.flatnonzero(flight_changed) + 1))
        end_rows = np.concatenate((start_rows[1:], [len(units)]))
        rul_values = h5_file["Y_dev"][start_rows, 0]

    return [
        FlightSegment(
            unit=int(units[start]),
            cycle=int(cycles[start]),
            start_row=int(start),
            end_row=int(end),
            rul=float(rul),
        )
        for start, end, rul in zip(start_rows, end_rows, rul_values)
    ]


def print_flight_summary(flights: list[FlightSegment]) -> None:
    flight_counts: dict[int, int] = {}

    for flight in flights:
        flight_counts[flight.unit] = flight_counts.get(flight.unit, 0) + 1

    print(f"\nTotal flights: {len(flights)}")

    for unit, count in sorted(flight_counts.items()):
        print(f"  Unit {unit}: {count} flights")
