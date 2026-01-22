import random
from models.household import Household
from storage.household_store import HouseholdStore

class HouseholdService:
    """
    Business logic for household registration and balance management.
    """

    def __init__(self, household_store: HouseholdStore):
        self.household_store = household_store
        
        # In-memory index for O(1) lookups
        self.households_by_id: dict[str, Household] = {}

    def bootstrap_from_file(self) -> None:
        """Load existing households on startup to support server reboot."""
        households = self.household_store.load_all()
        for h in households:
            self.households_by_id[h.household_id] = h

    def _generate_household_id(self) -> str:
        """
        Generate unique ID: H + 6 digits (e.g., H123456).
        Ensures no collisions.
        """
        while True:
            candidate = f"H{random.randint(100000, 999999)}"
            if candidate not in self.households_by_id:
                return candidate

    def register_household(self, address: str) -> Household:
        """
        Register a new household.
        1. Validate address.
        2. Generate ID.
        3. Assign full voucher entitlement ($800).
        4. Persist to storage.
        """
        if not address or not str(address).strip():
            raise ValueError("Address is required.")

        h_id = self._generate_household_id()

        # Business Logic: Entitlement Calculation
        # May 2025 ($500) + Jan 2026 ($300)
        # Breakdown: 80x$2, 32x$5, 45x$10
        initial_vouchers = {
            "2": 80,
            "5": 32,
            "10": 45
        }

        household = Household(
            household_id=h_id,
            address=str(address).strip(),
            balance=800,
            vouchers=initial_vouchers,
            link=f"http://cdc.gov.sg/claim/{h_id}"
        )

        # Persist to disk and update memory
        self.household_store.save(household)
        self.households_by_id[h_id] = household

        return household

    def get_household(self, household_id: str) -> Household:
        """
        Helper method to retrieve a household object by ID.
        Returns None if not found.
        """
        return self.households_by_id.get(household_id)

    def deduct_balance(self, household_id: str, amount: int) -> None:
        """
        Deducts balance from a household and saves the change to JSON.
        Raises ValueError if funds are insufficient.
        """
        household = self.get_household(household_id)
        if not household:
            raise ValueError("Household not found")
        
        if household.balance < amount:
            raise ValueError("Insufficient balance")

        # Update Memory
        household.balance -= amount
        
        # Persist to Disk immediately
        self.household_store.save(household)