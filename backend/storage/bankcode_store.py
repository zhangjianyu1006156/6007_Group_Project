import csv
from pathlib import Path

class BankCodeStore:
    """
    Simple loader/validator for BankCode.csv.
    We only need to validate (bank_code, branch_code) existence.
    """

    def __init__(self, bankcode_csv_path: Path):
        self.bankcode_csv_path = bankcode_csv_path
        self._pairs: set[tuple[str, str]] = set()

    def load(self) -> None:
        """Load BankCode.csv into an in-memory set for O(1) validation."""
        self._pairs.clear()

        with self.bankcode_csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bank_code = (row.get("Bank_Code") or "").strip()
                branch_code = (row.get("Branch_Code") or "").strip()
                if bank_code and branch_code:
                    self._pairs.add((bank_code, branch_code))

    def is_valid(self, bank_code: str, branch_code: str) -> bool:
        """Check if (bank_code, branch_code) exists in BankCode.csv."""
        return (bank_code.strip(), branch_code.strip()) in self._pairs
