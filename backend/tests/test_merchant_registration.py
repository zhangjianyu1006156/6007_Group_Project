"""
Simple integration-style tests for Merchant Registration.

How to run (from backend/ directory):
  python -m tests.test_merchant_registration

This script tests 4 cases:
1) Successful registration
2) Missing required field
3) Invalid bank_code / branch_code
4) Duplicate UEN
"""

from pathlib import Path
import shutil

from storage.bankcode_store import BankCodeStore
from storage.merchant_store import MerchantStore
from services.merchant_service import MerchantService


def _make_service(tmp_dir: Path) -> MerchantService:
    """
    Create a MerchantService instance using:
    - real BankCode.csv from storage/data/
    - temporary Merchant.txt in a tmp test folder
    """
    base_dir = Path(__file__).resolve().parents[1]  # backend/
    bankcode_path = base_dir / "storage" / "data" / "BankCode.csv"

    # Use a temp Merchant file for tests so we don't pollute real data
    merchant_path = tmp_dir / "Merchant.txt"

    bank_store = BankCodeStore(bankcode_path)
    bank_store.load()

    merchant_store = MerchantStore(merchant_path)
    service = MerchantService(merchant_store, bank_store)
    service.bootstrap_from_file()
    return service


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_success_registration() -> None:
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    service = _make_service(tmp_dir)

    payload = {
        "merchant_name": "ABC Minimart",
        "uen": "201234567A",
        "bank_name": "DBS Bank Ltd",
        "bank_code": "7171",   # should exist in the sample BankCode.csv
        "branch_code": "001",  # should exist in the sample BankCode.csv
        "account_number": "123-456-789",
        "account_holder_name": "ABC Minimart Pte Ltd",
        "status": "Active",
    }

    merchant = service.register_merchant(payload)

    _assert_true(merchant.merchant_id.startswith("M"), "merchant_id should start with 'M'")
    _assert_true(merchant.uen == payload["uen"], "UEN should match input payload")

    # Verify file written
    merchant_file = tmp_dir / "Merchant.txt"
    _assert_true(merchant_file.exists(), "Merchant.txt should be created")
    lines = merchant_file.read_text(encoding="utf-8").strip().splitlines()
    _assert_true(len(lines) >= 2, "Merchant.txt should contain header + at least 1 data row")


def test_missing_required_field() -> None:
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    service = _make_service(tmp_dir)

    payload = {
        "merchant_name": "Missing UEN Shop",
        # "uen": "xxxx",  # intentionally missing
        "bank_name": "DBS Bank Ltd",
        "bank_code": "7171",
        "branch_code": "001",
        "account_number": "111",
        "account_holder_name": "Someone",
    }

    try:
        service.register_merchant(payload)
        raise AssertionError("Expected ValueError for missing required field, but no error was raised.")
    except ValueError as e:
        _assert_true("Missing required field" in str(e), "Error message should mention missing required field.")


def test_invalid_bank_branch() -> None:
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    service = _make_service(tmp_dir)

    payload = {
        "merchant_name": "Invalid Bank Shop",
        "uen": "201234999Z",
        "bank_name": "Some Bank",
        "bank_code": "9999",  # invalid
        "branch_code": "999", # invalid
        "account_number": "222",
        "account_holder_name": "Invalid Bank Shop Pte Ltd",
    }

    try:
        service.register_merchant(payload)
        raise AssertionError("Expected ValueError for invalid bank/branch, but no error was raised.")
    except ValueError as e:
        _assert_true("Invalid bank_code / branch_code" in str(e), "Error message should mention invalid bank/branch.")


def test_duplicate_uen() -> None:
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    service = _make_service(tmp_dir)

    payload1 = {
        "merchant_name": "Shop One",
        "uen": "201200000A",
        "bank_name": "DBS Bank Ltd",
        "bank_code": "7171",
        "branch_code": "001",
        "account_number": "333",
        "account_holder_name": "Shop One Pte Ltd",
    }

    payload2 = {
        "merchant_name": "Shop Two",
        "uen": "201200000A",  # same UEN
        "bank_name": "DBS Bank Ltd",
        "bank_code": "7171",
        "branch_code": "001",
        "account_number": "444",
        "account_holder_name": "Shop Two Pte Ltd",
    }

    service.register_merchant(payload1)

    try:
        service.register_merchant(payload2)
        raise AssertionError("Expected ValueError for duplicate UEN, but no error was raised.")
    except ValueError as e:
        _assert_true("UEN already registered" in str(e), "Error message should mention duplicate UEN.")


def cleanup_tmp() -> None:
    """Remove temporary test folder."""
    tmp_dir = Path(__file__).resolve().parent / "_tmp"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


def main() -> None:
    cleanup_tmp()

    tests = [
        ("success registration", test_success_registration),
        ("missing required field", test_missing_required_field),
        ("invalid bank/branch", test_invalid_bank_branch),
        ("duplicate UEN", test_duplicate_uen),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    cleanup_tmp()
    print(f"\nResult: {passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    main()
