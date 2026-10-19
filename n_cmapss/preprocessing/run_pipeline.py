from .config import WINDOW_SIZE
from .create_folds import save_split_folds
from .create_windows import (
    build_window_records,
    save_window_metadata,
)
from .discover_flights import (
    discover_flights,
    print_flight_summary,
)
from .inspect_data import (
    inspect_dataset,
    validate_dataset_structure,
    validate_paths,
)


def main() -> None:
    validate_paths()
    inspect_dataset()
    validate_dataset_structure()

    flights = discover_flights()
    print_flight_summary(flights)

    windows = build_window_records(flights)
    metadata_path = save_window_metadata(windows)
    used_rows = len(windows) * WINDOW_SIZE

    print(f"\nWindows created: {len(windows):,}")
    print(f"Rows selected: {used_rows:,}")
    print(f"Metadata saved: {metadata_path}")

    split_path = save_split_folds(flights)
    print(f"Split configuration saved: {split_path}")


if __name__ == "__main__":
    main()
