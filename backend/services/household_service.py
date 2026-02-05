import random
import re
from models.household import Household
from storage.household_store import HouseholdStore

class HouseholdService:
    """
    Business logic for household registration and balance management.
    """

    def __init__(self, household_store: HouseholdStore):
        self.household_store = household_store
        
        self.households_by_id: dict[str, Household] = {}

    def bootstrap_from_file(self) -> None:
        """Load existing households on startup to support server reboot."""
        households = self.household_store.load_all()
        for h in households:
            self.households_by_id[h.household_id] = h

    def register_household(self, household_id: str, postal_code: str, unit_number: str) -> Household:
        """
        Register a new household with strict format validation.
        """
        # 1. Validate Inputs exist
        if not household_id or not str(household_id).strip():
            raise ValueError("Household ID is required.")
        
        postal = str(postal_code).strip()
        unit = str(unit_number).strip()

        if not postal:
            raise ValueError("Postal Code is required.")
        if not unit:
            raise ValueError("Unit Number is required.")

        # 2. Format Validation
        if not re.match(r"^\d{6}$", postal):
            raise ValueError("Invalid Postal Code. Must be exactly 6 digits (e.g. 560456).")

        if not re.match(r"^#\d{1,3}-\d{1,5}$", unit):
            raise ValueError("Invalid Unit Number. Must be in format #08-02 (Start with #).")

        # 3. Check for Duplicates
        h_id = str(household_id).strip()
        if h_id in self.households_by_id:
            raise ValueError("Household ID already exists.")

        # 4. Create Household
        initial_vouchers = {
            "2": 80,
            "5": 32,
            "10": 45
        }

        calculated_balance = sum(int(denom) * qty for denom, qty in initial_vouchers.items())

        household = Household(
            household_id=h_id,
            postal_code=postal,
            unit_number=unit,
            balance=calculated_balance,
            vouchers=initial_vouchers,
            link=f"http://cdc.gov.sg/claim/{h_id}"
        )

        # 5. Save
        self.household_store.save(household)
        self.households_by_id[h_id] = household

        return household

    def get_household(self, household_id: str) -> Household:
        return self.households_by_id.get(household_id)

    def deduct_balance(self, household_id: str, amount: int) -> None:
        household = self.get_household(household_id)
        if not household:
            raise ValueError("Household not found")
        
        if household.balance < amount:
            raise ValueError("Insufficient balance")

        household.balance -= amount
        self.household_store.save(household)