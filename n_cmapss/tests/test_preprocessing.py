import io
import unittest
from contextlib import redirect_stdout

from n_cmapss.preprocessing.config import DATA_PATH
from n_cmapss.preprocessing.validate_outputs import (
    validate_data_loader,
    validate_output_files,
    validate_split_folds,
    validate_window_metadata,
    validate_windows_against_hdf5,
)


@unittest.skipUnless(DATA_PATH.exists(), "N-CMAPSS HDF5 file is not available")
class PreprocessingValidationTests(unittest.TestCase):
    def run_silently(self, validation_function) -> None:
        with redirect_stdout(io.StringIO()):
            validation_function()

    def test_output_files(self) -> None:
        self.run_silently(validate_output_files)

    def test_window_metadata(self) -> None:
        self.run_silently(validate_window_metadata)

    def test_windows_match_hdf5(self) -> None:
        self.run_silently(validate_windows_against_hdf5)

    def test_split_folds(self) -> None:
        self.run_silently(validate_split_folds)

    def test_all_windows_load(self) -> None:
        self.run_silently(validate_data_loader)


if __name__ == "__main__":
    unittest.main()
