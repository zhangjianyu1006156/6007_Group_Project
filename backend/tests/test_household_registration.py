"""
Tests for Household Registration.
Run from backend/ directory:
python -m tests.test_household
"""

from pathlib import Path
import shutil
from storage.household_store import HouseholdStore
from services.household_service import HouseholdService

def test_household_registration():
    # Setup temporary test folder
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Service with temp file
    store = HouseholdStore(tmp_dir / "households.json")
    service = HouseholdService(store)
    service.bootstrap_from_file()

    # Test Case 1: Success
    print("Testing Valid Registration...", end=" ")
    h = service.register_household("Block 123 Bedok North")
    assert h.household_id.startswith("H"), "ID must start with H"
    assert h.balance == 800, "Balance must be 800"
    assert h.vouchers["10"] == 45, "Should have 45 $10 vouchers"
    print("PASS")

    # Test Case 2: Missing Address
    print("Testing Missing Address...", end=" ")
    try:
        service.register_household("")
        print("FAIL (Should have raised error)")
    except ValueError:
        print("PASS")

    # Cleanup
    shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    test_household_registration()