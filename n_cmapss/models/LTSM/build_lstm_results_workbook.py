from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = PROJECT_ROOT / "processed" / "experiments"
OUTPUT_PATH = EXPERIMENT_DIR / "lstm_detailed_results.xlsx"


def format_sheet(writer: pd.ExcelWriter, sheet_name: str) -> None:
    worksheet = writer.sheets[sheet_name]

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    for column_index, column in enumerate(worksheet.columns, start=1):
        max_length = max(
            len(str(worksheet.cell(row=row_index, column=column_index).value or ""))
            for row_index in range(1, worksheet.max_row + 1)
        )
        worksheet.column_dimensions[get_column_letter(column_index)].width = min(
            max(max_length + 2, 12),
            32,
        )


def main() -> None:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(EXPERIMENT_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSV deneyi bulunamadı: {EXPERIMENT_DIR}")

    raw_frames: dict[str, pd.DataFrame] = {}
    summary_frames: list[pd.DataFrame] = []

    for csv_path in csv_files:
        frame = pd.read_csv(csv_path)
        sheet_name = csv_path.stem[:31].replace(" ", "_")
        raw_frames[sheet_name] = frame

        numeric_columns = frame.select_dtypes(include="number").columns
        value_columns = [
            column
            for column in ("mae", "rmse", "val_mae", "val_rmse", "val_mse")
            if column in numeric_columns
        ]

        if value_columns:
            parameter_columns = [
                column
                for column in (
                    "seed", "batch_size", "dropout", "learning_rate", "units",
                    "model", "motor", "validation_motor", "fold",
                )
                if column in frame.columns
            ]
            summary_columns = [
                column
                for column in parameter_columns
                if column not in ("motor", "validation_motor", "fold")
            ]

            if summary_columns:
                summary = (
                    frame.groupby(summary_columns, dropna=False)[value_columns]
                    .agg(["mean", "std", "count"])
                    .reset_index()
                )
                summary.columns = [
                    "_".join(filter(None, (str(level1), str(level2))))
                    if level2
                    else str(level1)
                    for level1, level2 in summary.columns
                ]
                summary.insert(0, "deney", csv_path.stem)
                summary_frames.append(summary)

    motor_frames: list[pd.DataFrame] = []
    for csv_path in csv_files:
        frame = pd.read_csv(csv_path)
        motor_column = (
            "motor" if "motor" in frame.columns
            else "validation_motor" if "validation_motor" in frame.columns
            else None
        )
        mae_column = (
            "mae" if "mae" in frame.columns
            else "val_mae" if "val_mae" in frame.columns
            else None
        )

        if motor_column and mae_column:
            motor = frame[[motor_column, mae_column]].copy()
            motor.columns = ["motor", "mae"]
            motor.insert(0, "deney", csv_path.stem)
            motor_frames.append(motor)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "Bilgi": [
                    "Bu çalışma, mevcut CSV deneme sonuçlarını tek Excel dosyasına toplar.",
                    "Ham sonuçlar tek tek CSV dosyalarından korunmuştur.",
                    "Özet sayfaları betimsel istatistik sağlar; yeni eğitimleri sonuçlandırmaz.",
                    "Gerçek karşılaştırma için seed, batch, dropout ve learning rate aynı protokolle yeniden çalıştırılmalıdır.",
                    "Leave-one-motor-out doğrulama kullanılır; eğitim ve doğrulama motorları ayrıdır.",
                ]
            }
        ).to_excel(writer, sheet_name="Aciklama", index=False)

        for sheet_name, frame in raw_frames.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)

        if summary_frames:
            pd.concat(summary_frames, ignore_index=True).to_excel(
                writer, sheet_name="Ozet_Istatistik", index=False
            )

        if motor_frames:
            motor_all = pd.concat(motor_frames, ignore_index=True)
            motor_all.to_excel(writer, sheet_name="Motor_Ham_Sonuclar", index=False)

            motor_summary = (
                motor_all.groupby(["motor", "deney"], dropna=False)["mae"]
                .agg(["mean", "std", "count"])
                .reset_index()
                .sort_values(["motor", "mean"])
            )
            motor_summary.to_excel(writer, sheet_name="Motor_Ozet", index=False)

        for sheet_name in writer.sheets:
            format_sheet(writer, sheet_name)

    print(f"Excel raporu oluşturuldu: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
