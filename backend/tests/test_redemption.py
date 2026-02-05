#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 16:10:32 2026

@author: richardfeng
"""

"""
Simple integration-style tests for Redemption.

How to run (from backend/ directory):
  python -m tests.test_redemption

What this script tests:
1) Successful redemption (end-to-end): generate_code -> redeem -> write RedeemYYYYMMDDHH.csv
2) Invalid code
3) Expired code (TTL)
4) Reused code (single-use)
5) Inactive merchant
6) Insufficient vouchers at redemption time (simulate wallet change after code generation)

Notes:
- Uses real BankCode.csv from storage/data/ for merchant registration validation.
- Uses temporary files/folders so it won't pollute real data:
  - Merchant.txt
  - households.json
  - counters.json
  - RedeemYYYYMMDDHH.csv
"""


from pathlib import Path
import shutil
from datetime import datetime, timedelta

from storage.bankcode_store import BankCodeStore
from storage.merchant_store import MerchantStore
from storage.household_store import HouseholdStore
from storage.counter_store import CounterStore
from storage.redemption_store import RedemptionStore

from services.merchant_service import MerchantService
from services.household_service import HouseholdService
from services.redemption_service import RedemptionService


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _new_case_dir(case_name: str) -> Path:
    """Create an isolated temp dir for a single test case."""
    root = Path(__file__).resolve().parent / "_tmp_redemption"
    case_dir = root / case_name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def _cleanup_all() -> None:
    """Remove all temporary redemption test folders."""
    root = Path(__file__).resolve().parent / "_tmp_redemption"
    if root.exists():
        shutil.rmtree(root)


def _make_env(tmp_dir: Path):
    """
    Build stores/services exactly like app.py, but all persisted files go into tmp_dir.
    Returns:
      merchant_service, household_service, redemption_service, pending_codes
    """
    base_dir = Path(__file__).resolve().parents[1] 
    bankcode_path = base_dir / "storage" / "data" / "BankCode.csv"

    bank_store = BankCodeStore(bankcode_path)
    bank_store.load()

    merchant_store = MerchantStore(tmp_dir / "Merchant.txt")
    household_store = HouseholdStore(tmp_dir / "households.json")
    counter_store = CounterStore(tmp_dir / "counters.json")
    redemption_store = RedemptionStore(tmp_dir)

    if hasattr(counter_store, "load"):
        try:
            counter_store.load()
        except Exception:
            pass

    # Services
    merchant_service = MerchantService(merchant_store, bank_store)
    merchant_service.bootstrap_from_file()

    household_service = HouseholdService(household_store)
    household_service.bootstrap_from_file()

    pending_codes = {}

    redemption_service = RedemptionService(
        household_service=household_service,
        household_store=household_store,
        merchant_service=merchant_service,
        counter_store=counter_store,
        redemption_store=redemption_store,
        pending_codes=pending_codes,
        code_ttl_seconds=600,
    )

    return merchant_service, household_service, redemption_service, pending_codes


def _seed_household_and_merchant(tmp_dir: Path):
    """Create 1 valid household and 1 valid merchant for redemption tests."""
    merchant_service, household_service, redemption_service, pending_codes = _make_env(tmp_dir)

    # 1) Household
    household = household_service.register_household(
        household_id="H52298800781",
        postal_code="560123",
        unit_number="#06-03",
    )

    # 2) Merchant
    merchant = merchant_service.register_merchant({
        "merchant_name": "ABC Minimart",
        "uen": "201234567A",
        "bank_name": "DBS Bank Ltd",
        "bank_code": "7171",
        "branch_code": "001",
        "account_number": "123-456-789",
        "account_holder_name": "ABC Minimart Pte Ltd",
        "status": "Active",
    })

    return merchant_service, household_service, redemption_service, pending_codes, household, merchant


# -------------------------
# Test Cases
# -------------------------
def test_success_redemption() -> None:
    tmp_dir = _new_case_dir("success_redemption")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    selected = {"10": 1, "5": 2} 
    code = redemption_service.generate_code(household.household_id, selected)

    result = redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)

    _assert_true(result.get("amount_redeemed") == 20, "amount_redeemed should be 20 (10*1 + 5*2)")
    _assert_true(result.get("remaining_balance") == household.balance, "remaining_balance should match updated household.balance")
    _assert_true(code not in pending_codes, "code should be removed after successful redemption (single-use)")

    redeem_files = list(tmp_dir.glob("Redeem*.csv"))
    _assert_true(len(redeem_files) == 1, f"Expected exactly 1 Redeem*.csv file, got {len(redeem_files)}")

    lines = redeem_files[0].read_text(encoding="utf-8").strip().splitlines()
    _assert_true(len(lines) == 1 + 3, f"Expected header + 3 rows, got {len(lines)} lines")
    _assert_true("Transaction_ID" in lines[0], "First line should be CSV header containing 'Transaction_ID'")


def test_invalid_code() -> None:
    tmp_dir = _new_case_dir("invalid_code")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    try:
        redemption_service.redeem(merchant_id=merchant.merchant_id, code="000000")
        raise AssertionError("Expected ValueError for invalid code, but no error was raised.")
    except ValueError as e:
        _assert_true("Invalid code" in str(e), "Error message should mention invalid code.")


def test_expired_code() -> None:
    tmp_dir = _new_case_dir("expired_code")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    code = redemption_service.generate_code(household.household_id, {"10": 1})

    pending_codes[code]["created_at"] = (datetime.now() - timedelta(seconds=9999)).isoformat()

    try:
        redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)
        raise AssertionError("Expected ValueError for expired code, but no error was raised.")
    except ValueError as e:
        _assert_true("Code expired" in str(e), "Error message should mention code expired.")
        _assert_true(code not in pending_codes, "Expired code should be removed from pending_codes.")


def test_reused_code() -> None:
    tmp_dir = _new_case_dir("reused_code")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    code = redemption_service.generate_code(household.household_id, {"10": 1})
    redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)

    try:
        redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)
        raise AssertionError("Expected ValueError for reused code, but no error was raised.")
    except ValueError as e:
        _assert_true("Invalid code" in str(e), "Reused code should behave like invalid code (already popped).")


def test_inactive_merchant() -> None:
    tmp_dir = _new_case_dir("inactive_merchant")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    merchant.status = "Inactive"

    code = redemption_service.generate_code(household.household_id, {"10": 1})

    try:
        redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)
        raise AssertionError("Expected ValueError for inactive merchant, but no error was raised.")
    except ValueError as e:
        _assert_true("not active" in str(e).lower(), "Error message should mention merchant is not active.")


def test_insufficient_vouchers_at_redemption_time() -> None:
    tmp_dir = _new_case_dir("insufficient_at_redeem")

    merchant_service, household_service, redemption_service, pending_codes, household, merchant = _seed_household_and_merchant(tmp_dir)

    code = redemption_service.generate_code(household.household_id, {"10": 1})
    household.vouchers["10"] = 0

    try:
        redemption_service.redeem(merchant_id=merchant.merchant_id, code=code)
        raise AssertionError("Expected ValueError for insufficient vouchers at redemption time, but no error was raised.")
    except ValueError as e:
        _assert_true("Insufficient vouchers" in str(e), "Error message should mention insufficient vouchers.")


def main() -> None:
    _cleanup_all()

    tests = [
        ("success redemption", test_success_redemption),
        ("invalid code", test_invalid_code),
        ("expired code", test_expired_code),
        ("reused code", test_reused_code),
        ("inactive merchant", test_inactive_merchant),
        ("insufficient vouchers at redemption", test_insufficient_vouchers_at_redemption_time),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    print(f"\nResult: {passed}/{len(tests)} tests passed.")

if __name__ == "__main__":
    main()
