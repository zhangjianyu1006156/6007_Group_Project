from dataclasses import dataclass, asdict

@dataclass
class Household:
    """
    Household domain model.
    Encapsulates the wallet data.
    """
    household_id: str
    address: str
    balance: int
    vouchers: dict[str, int]  # e.g. {"2": 80, "5": 32, "10": 45}
    link: str

    def to_dict(self) -> dict:
        """Convert object to dictionary for JSON storage."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Household":
        """Reconstruct object from dictionary."""
        return Household(
            household_id=data.get("household_id") or data.get("id"), # Handle potential key diffs
            address=data["address"],
            balance=data["balance"],
            vouchers=data["vouchers"],
            link=data["link"]
        )