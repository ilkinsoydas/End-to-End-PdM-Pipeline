"""Export existing DS02 windows with unscaled loader values (float32).

From the repository root, with the project environment active:
    python -m pip install XlsxWriter openpyxl
    python -m n_cmapss.export_window_excel

Output: n_cmapss/processed/window_excel/unit_<unit>_windows.xlsx.
start_row is inclusive, end_row exclusive, and time_step starts at zero.
Window_Summary uses all 256 observations (population standard deviation).
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from openpyxl import load_workbook
from xlsxwriter import Workbook

from .preprocessing.config import OUTPUT_DIR, WINDOW_SIZE
from .preprocessing.data_loader import NCmapssDataLoader, load_feature_names, load_window_metadata

UNITS = (2, 5, 10, 16, 18, 20)
MAX_ROWS = 1_048_576
WINDOWS_PER_SHEET = (MAX_ROWS - 1) // WINDOW_SIZE


def stats(features):
    """Population standard deviation across all time steps (ddof=0)."""
    means = features.mean(axis=0, dtype=np.float64)
    stds = features.std(axis=0, dtype=np.float64, ddof=0)
    return np.column_stack((means, stds)).ravel().tolist()


def export(path, records, names, loader):
    data_header = ["window_id", "unit", "cycle", "rul", "time_step", *names]
    summary_header = ["window_id", "unit", "cycle", "rul", "start_row", "end_row"]
    summary_header += [f"{name}_{stat}" for name in names for stat in ("mean", "std")]
    if len(records) + 1 > MAX_ROWS:
        raise ValueError("Summary exceeds Excel row limit")

    with Workbook(path, {"constant_memory": True, "tmpdir": str(path.parent)}) as book:
        heading = book.add_format({"bold": True, "font_color": "white", "bg_color": "#234963"})
        decimals = book.add_format({"num_format": "0.000000"})

        def sheet(title, header, count, identifiers):
            page = book.add_worksheet(title)
            page.write_row(0, 0, header, heading)
            page.freeze_panes(1, 1)
            page.autofilter(0, 0, count, len(header) - 1)
            page.set_column(0, identifiers - 1, 14)
            page.set_column(identifiers, len(header) - 1, 17, decimals)
            return page

        for index, (record, features, target) in enumerate(loader.iter_windows(records)):
            position = index % WINDOWS_PER_SHEET
            if position == 0:
                chunk = index // WINDOWS_PER_SHEET + 1
                count = min(WINDOWS_PER_SHEET, len(records) - index)
                data = sheet("Window_Data" if chunk == 1 else f"Window_Data_{chunk}",
                             data_header, count * WINDOW_SIZE, 5)
                if index == 0:
                    summary = sheet("Window_Summary", summary_header, len(records), 6)
            if (record != records[index] or record.end_row - record.start_row != WINDOW_SIZE
                    or target != record.rul or not np.isfinite(features).all()):
                raise ValueError(f"Invalid window {record.window_id}")
            keys = [record.window_id, record.unit, record.cycle, record.rul]
            for step, values in enumerate(features.tolist()):
                data.write_row(1 + position * WINDOW_SIZE + step, 0, [*keys, step, *values])
            summary.write_row(index + 1, 0, [*keys, record.start_row, record.end_row, *stats(features)])


def verify(path, records, loader):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        summaries = book["Window_Summary"].iter_rows(min_row=2, values_only=True)
        for index, (record, row) in enumerate(zip(records, summaries, strict=True)):
            keys = (record.window_id, record.unit, record.cycle, record.rul)
            if row[:6] != (*keys, record.start_row, record.end_row):
                raise ValueError(f"Summary metadata mismatch: {record.window_id}")
            if record.unit == 5 and record.window_id in (854, 859):
                start = 2 + (index % WINDOWS_PER_SHEET) * WINDOW_SIZE
                chunk = index // WINDOWS_PER_SHEET + 1
                data = book["Window_Data" if chunk == 1 else f"Window_Data_{chunk}"]
                rows = data.iter_rows(min_row=start, max_row=start + WINDOW_SIZE - 1, values_only=True)
                expected, _ = loader.load_window(record)
                for step, (actual, source) in enumerate(zip(rows, expected, strict=True)):
                    if actual[:5] != (*keys, step):
                        raise ValueError(f"Data metadata mismatch: {record.window_id}")
                    np.testing.assert_array_equal(np.asarray(actual[5:], dtype=np.float32), source)
                np.testing.assert_allclose(row[6:], stats(expected), rtol=1e-12, atol=1e-12)
                print(f"Verified unit 5 / window {record.window_id}: 256 x 18 and summary", flush=True)
        for offset in range(0, len(records), WINDOWS_PER_SHEET):
            chunk = offset // WINDOWS_PER_SHEET + 1
            data = book["Window_Data" if chunk == 1 else f"Window_Data_{chunk}"]
            expected_count = min(len(records) - offset, WINDOWS_PER_SHEET) * WINDOW_SIZE
            if data.max_row != expected_count + 1 or data.max_column != 23:
                raise ValueError("Invalid Window_Data dimensions")
    finally:
        book.close()


def main():
    records = load_window_metadata()
    if len({r.window_id for r in records}) != len(records):
        raise ValueError("Duplicate window_id")
    if {r.unit for r in records} != set(UNITS):
        raise ValueError("Unexpected engine list")
    if not {854, 859} <= {r.window_id for r in records if r.unit == 5}:
        raise ValueError("Required unit 5 windows missing")

    names = load_feature_names()
    destination = OUTPUT_DIR / "window_excel"
    destination.mkdir(exist_ok=True)
    with NCmapssDataLoader() as loader, TemporaryDirectory(dir=destination) as work:
        for unit in UNITS:
            windows = [r for r in records if r.unit == unit]
            path = Path(work) / f"unit_{unit}_windows.xlsx"
            export(path, windows, names, loader)
            verify(path, windows, loader)
            path.replace(destination / path.name)
            print(f"Motor {unit:2}: {len(windows):4} pencere | {len(windows)*WINDOW_SIZE:,} zaman adımı", flush=True)
    print(f"Toplam: {len(records):,} pencere | {len(records)*WINDOW_SIZE:,} zaman adımı")


if __name__ == "__main__":
    main()
