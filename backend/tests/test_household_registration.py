import unittest
import shutil
from pathlib import Path
from services.household_service import HouseholdService
from storage.household_store import HouseholdStore

class TestHouseholdRegistration(unittest.TestCase):
    def setUp(self):
        # 1. Setup a temporary test folder so we don't mess up real data
        self.test_dir = Path("storage/test_data")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Initialize Store & Service with test path
        self.store = HouseholdStore(self.test_dir / "households_test.json")
        self.service = HouseholdService(self.store)

    def tearDown(self):
        # Clean up: Delete the test folder after every test
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_valid_registration(self):
        """Test that correct Singapore formats work."""
        h = self.service.register_household(
            household_id="H1001", 
            postal_code="560123",      # Valid: 6 digits
            unit_number="#06-03"       # Valid: Starts with #
        )
        self.assertEqual(h.household_id, "H1001")
        self.assertEqual(h.postal_code, "560123")
        self.assertEqual(h.balance, 800) # Check entitlement

    def test_invalid_postal_code(self):
        """Test that wrong postal codes trigger an error."""
        with self.assertRaises(ValueError) as context:
            self.service.register_household("H1002", "123", "#06-03") # Too short
        
        self.assertIn("Invalid Postal Code", str(context.exception))

    def test_invalid_unit_number(self):
        """Test that unit numbers without '#' fail."""
        with self.assertRaises(ValueError) as context:
            self.service.register_household("H1003", "123456", "06-03") # Missing #
        
        self.assertIn("Invalid Unit Number", str(context.exception))

    def test_duplicate_registration(self):
        """Test that you can't register the same ID twice."""
        self.service.register_household("H1004", "123456", "#01-01")
        
        with self.assertRaises(ValueError) as context:
            self.service.register_household("H1004", "654321", "#02-02")
            
        self.assertIn("already exists", str(context.exception))

if __name__ == "__main__":
    unittest.main()