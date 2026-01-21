from dataclasses import dataclass
from datetime import date

@dataclass
class Merchant:
    """
    Merchant domain model.

    Note: Field order matches the required Merchant.txt (CSV-like) format.
    """
    merchant_id: str
    merchant_name: str
    uen: str
    bank_name: str
    bank_code: str
    branch_code: str
    account_number: str
    account_holder_name: str
    registration_date: str  # YYYY-MM-DD
    status: str  # e.g., Active / Pending / Suspended

    @staticmethod
    def today_str() -> str:
        """Return today's date in ISO format (YYYY-MM-DD)."""
        return date.today().isoformat()

    def to_csv_row(self) -> list[str]:
        """Convert this Merchant object into a CSV row in the required order."""
        return [
            self.merchant_id,
            self.merchant_name,
            self.uen,
            self.bank_name,
            self.bank_code,
            self.branch_code,
            self.account_number,
            self.account_holder_name,
            self.registration_date,
            self.status,
        ]
