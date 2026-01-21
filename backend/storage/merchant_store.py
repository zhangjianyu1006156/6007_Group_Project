import csv
from pathlib import Path
from typing import Iterable
from models.merchant import Merchant

MERCHANT_HEADER = [
    "Merchant_ID",
    "Merchant_Name",
    "UEN",
    "Bank_Name",
    "Bank_Code",
    "Branch_Code",
    "Account_Number",
    "Account_Holder_Name",
    "Registration_Date",
    "Status",
]

class MerchantStore:
    """
    File-based storage for merchants.
    The spec requires a .txt file; we store it in CSV format.
    """

    def __init__(self, merchant_file_path: Path):
        self.merchant_file_path = merchant_file_path

    def ensure_file_with_header(self) -> None:
        """Create file + header if not exists or empty."""
        if not self.merchant_file_path.exists() or self.merchant_file_path.stat().st_size == 0:
            self.merchant_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.merchant_file_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(MERCHANT_HEADER)

    def append(self, merchant: Merchant) -> None:
        """Append one merchant record to Merchant.txt."""
        self.ensure_file_with_header()
        with self.merchant_file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(merchant.to_csv_row())

    def load_all(self) -> list[Merchant]:
        """
        Load all merchants from Merchant.txt.
        Useful for server restart recovery and ID uniqueness checks.
        """
        if not self.merchant_file_path.exists():
            return []

        merchants: list[Merchant] = []
        with self.merchant_file_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                merchants.append(
                    Merchant(
                        merchant_id=(row.get("Merchant_ID") or "").strip(),
                        merchant_name=(row.get("Merchant_Name") or "").strip(),
                        uen=(row.get("UEN") or "").strip(),
                        bank_name=(row.get("Bank_Name") or "").strip(),
                        bank_code=(row.get("Bank_Code") or "").strip(),
                        branch_code=(row.get("Branch_Code") or "").strip(),
                        account_number=(row.get("Account_Number") or "").strip(),
                        account_holder_name=(row.get("Account_Holder_Name") or "").strip(),
                        registration_date=(row.get("Registration_Date") or "").strip(),
                        status=(row.get("Status") or "").strip(),
                    )
                )
        return merchants
