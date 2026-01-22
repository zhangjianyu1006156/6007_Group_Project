from dataclasses import dataclass, asdict

@dataclass
class Household:
    """
    Household domain model.
    Encapsulates the wallet data and location info.
    """
    household_id: str
    postal_code: str
    unit_number: str
    balance: int
    vouchers: dict[str, int]
    link: str

    def to_dict(self) -> dict:
        """Convert object to dictionary for JSON storage."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Household":
        """Reconstruct object from dictionary."""
        return Household(
            household_id=data.get("household_id") or data.get("id"),
            postal_code=data.get("postal_code", ""),
            unit_number=data.get("unit_number", ""),
            balance=data["balance"],
            vouchers=data["vouchers"],
            link=data["link"]
        )