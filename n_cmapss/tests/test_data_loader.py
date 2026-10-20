import unittest

import numpy as np

from n_cmapss.preprocessing.config import DATA_PATH, WINDOW_SIZE
from n_cmapss.preprocessing.data_loader import (
    NCmapssDataLoader,
    load_feature_names,
    load_window_metadata,
    split_windows_by_fold,
)


@unittest.skipUnless(DATA_PATH.exists(), "N-CMAPSS HDF5 file is not available")
class DataLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.windows = load_window_metadata()

    def test_feature_names_are_in_expected_order(self) -> None:
        self.assertEqual(
            load_feature_names(),
            [
                "alt",
                "Mach",
                "TRA",
                "T2",
                "T24",
                "T30",
                "T48",
                "T50",
                "P15",
                "P2",
                "P21",
                "P24",
                "Ps30",
                "P40",
                "P50",
                "Nf",
                "Nc",
                "Wf",
            ],
        )

    def test_first_window_has_expected_shape_and_type(self) -> None:
        first_window = self.windows[0]

        with NCmapssDataLoader() as loader:
            features, target = loader.load_window(first_window)

        self.assertEqual(features.shape, (WINDOW_SIZE, 18))
        self.assertEqual(features.dtype, np.float32)
        self.assertEqual(target.dtype, np.float32)
        self.assertTrue(np.isfinite(features).all())
        self.assertTrue(np.isfinite(target))
        self.assertEqual(float(target), first_window.rul)

    def test_fold_one_separates_engines(self) -> None:
        train_windows, validation_windows = split_windows_by_fold(
            self.windows,
            fold_number=1,
        )

        train_units = {window.unit for window in train_windows}
        validation_units = {window.unit for window in validation_windows}

        self.assertEqual(train_units, {5, 10, 16, 18, 20})
        self.assertEqual(validation_units, {2})
        self.assertTrue(train_units.isdisjoint(validation_units))
        self.assertEqual(
            len(train_windows) + len(validation_windows),
            len(self.windows),
        )

    def test_first_batch_has_expected_shape_and_type(self) -> None:
        train_windows, _ = split_windows_by_fold(
            self.windows,
            fold_number=1,
        )

        with NCmapssDataLoader() as loader:
            features, targets, records = next(
                loader.iter_batches(train_windows, batch_size=64)
            )

        self.assertEqual(features.shape, (64, WINDOW_SIZE, 18))
        self.assertEqual(targets.shape, (64,))
        self.assertEqual(features.dtype, np.float32)
        self.assertEqual(targets.dtype, np.float32)
        self.assertEqual(len(records), 64)

    def test_invalid_fold_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_windows_by_fold(self.windows, fold_number=99)

    def test_loader_requires_context_manager(self) -> None:
        loader = NCmapssDataLoader()

        with self.assertRaises(RuntimeError):
            loader.load_window(self.windows[0])

    def test_invalid_batch_size_is_rejected(self) -> None:
        with NCmapssDataLoader() as loader:
            with self.assertRaises(ValueError):
                next(loader.iter_batches(self.windows, batch_size=0))


if __name__ == "__main__":
    unittest.main()
