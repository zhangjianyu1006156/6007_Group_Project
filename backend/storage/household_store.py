import json
from pathlib import Path
from models.household import Household

class HouseholdStore:
    """
    File-based storage for households using JSON.
    """

    def __init__(self, household_file_path: Path):
        self.household_file_path = household_file_path

    def _load_data(self) -> dict:
        """Internal helper to read raw JSON safely."""
        if not self.household_file_path.exists():
            return {}
        try:
            with self.household_file_path.open("r", encoding="utf-8") as f:
                # Handle empty files
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_data(self, data: dict) -> None:
        """Internal helper to write raw JSON."""
        self.household_file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.household_file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def save(self, household: Household) -> None:
        """Save or update a single household."""
        data = self._load_data()
        # Store using ID as key for easy lookup
        data[household.household_id] = household.to_dict()
        self._save_data(data)

    def load_all(self) -> list[Household]:
        """Load all households into memory (for bootstrapping)."""
        data = self._load_data()
        households = []
        for h_data in data.values():
            households.append(Household.from_dict(h_data))
        return households