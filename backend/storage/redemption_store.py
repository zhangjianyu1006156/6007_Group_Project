import csv
from datetime import datetime
from pathlib import Path


REDEEM_HEADER = [
    "Transaction_ID",
    "Household_ID",
    "Merchant_ID",
    "Transaction_Date_Time",
    "Voucher_Code",
    "Denomination_Used",
    "Amount_Redeemed",
    "Payment_Status",
    "Remarks",
]


class RedemptionStore:
    """
    Handles writing redemption logs to hourly CSV:
    RedeemYYYYMMDDHH.csv
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _file_path(self) -> Path:
        filename = f"Redeem{datetime.now().strftime('%Y%m%d%H')}.csv"
        return self.data_dir / filename

    def append_row(self, row: list[str]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self._file_path()

        need_header = (not path.exists()) or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if need_header:
                writer.writerow(REDEEM_HEADER)
            writer.writerow(row)