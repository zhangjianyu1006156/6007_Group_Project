import random
from datetime import datetime, timedelta

from services.household_service import HouseholdService
from services.merchant_service import MerchantService
from storage.household_store import HouseholdStore
from storage.counter_store import CounterStore
from storage.redemption_store import RedemptionStore


class RedemptionService:
    """
    Redemption business logic ONLY (no file I/O here):
    - Validate merchant_id
    - Validate redemption code (pending_codes in memory)
    - Deduct vouchers & balance from household
    - Persist household JSON via HouseholdStore
    - Write redemption logs via RedemptionStore
    - Generate TX/V codes via CounterStore
    """

    def __init__(
        self,
        household_service: HouseholdService,
        household_store: HouseholdStore,
        merchant_service: MerchantService,
        counter_store: CounterStore,
        redemption_store: RedemptionStore,
        pending_codes: dict,
        code_ttl_seconds: int = 600,
    ):
        self.household_service = household_service
        self.household_store = household_store
        self.merchant_service = merchant_service
        self.counter_store = counter_store
        self.redemption_store = redemption_store
        self.pending_codes = pending_codes
        self.code_ttl_seconds = code_ttl_seconds

    def generate_code(self, household_id: str, vouchers: dict) -> str:
        """
        Generates a 6-digit OTP for the specified vouchers.
        Validates that the household exists and has sufficient balance.
        """
        # 1. Validate Household
        household = self.household_service.households_by_id.get(household_id)
        if not household:
            raise ValueError("Household not found.")

        # 2. Validate Voucher Balance
        if not self._has_sufficient_vouchers(household.vouchers, vouchers):
            raise ValueError("Insufficient vouchers.")

        # 3. Generate Code
        code = str(random.randint(100000, 999999))
        while code in self.pending_codes:
            code = str(random.randint(100000, 999999))

        # 4. Store in memory
        self.pending_codes[code] = {
            "household_id": household_id,
            "vouchers": vouchers,
            "created_at": datetime.now().isoformat()
        }
        return code

    def redeem(self, merchant_id: str, code: str) -> dict:
        merchant_id = (merchant_id or "").strip()
        code = (code or "").strip()

        if not merchant_id or not code:
            raise ValueError("merchant_id and code are required.")

        # 1) Validate merchant exists + active
        merchant = self.merchant_service.merchants_by_id.get(merchant_id)
        if not merchant:
            raise ValueError("Invalid merchant.")

        if (merchant.status or "").strip().lower() != "active":
            raise ValueError("Merchant is not active.")

        # 2) Validate code exists + TTL
        txn = self.pending_codes.get(code)
        if not txn:
            raise ValueError("Invalid code.")

        created_dt = self._extract_created_time(txn)
        if created_dt is not None:
            if datetime.now() > created_dt + timedelta(seconds=self.code_ttl_seconds):
                self.pending_codes.pop(code, None)
                raise ValueError("Code expired. Please generate a new one.")

        household_id = (txn.get("household_id") or "").strip()
        selected_vouchers = txn.get("vouchers") or {}

        if not household_id:
            raise ValueError("Code data corrupted (missing household_id).")

        # 3) Load household from memory
        household = self.household_service.households_by_id.get(household_id)
        if not household:
            raise ValueError("Household not found.")

        # 4) Check voucher sufficiency
        if not self._has_sufficient_vouchers(household.vouchers, selected_vouchers):
            raise ValueError("Insufficient vouchers.")

        # 5) Compute total amount
        total = self._compute_total(selected_vouchers)
        if total <= 0:
            raise ValueError("Total amount must be > 0.")

        # 6) Deduct vouchers + balance
        self._deduct_from_household(household, selected_vouchers, total)

        # 7) Persist household JSON
        self.household_store.save(household)

        # 8) Write redemption logs (one row per voucher note)
        tx_id = self.counter_store.next_transaction_id()
        txn_time = datetime.now().strftime("%Y%m%d%H%M%S")  # required digits format

        total_items = sum(int(q) for q in selected_vouchers.values())
        counter = 1

        for denom, qty in selected_vouchers.items():
            denom = int(denom)
            for _ in range(int(qty)):
                voucher_code = self.counter_store.next_voucher_code()

                remark = str(counter)
                if counter == total_items:
                    remark = "Final denomination used"

                row = [
                    tx_id,
                    household_id,
                    merchant_id,
                    txn_time,
                    voucher_code,
                    f"${denom}.00",
                    f"${total}.00",
                    "Completed",
                    remark,
                ]
                self.redemption_store.append_row(row)
                counter += 1

        # 9) Single-use code
        self.pending_codes.pop(code, None)

        return {
            "transaction_id": tx_id,
            "household_id": household_id,
            "merchant_id": merchant_id,
            "amount_redeemed": total,
            "remaining_balance": household.balance,
        }

    # --------------------------
    # Helpers
    # --------------------------
    def _compute_total(self, selected: dict) -> int:
        total = 0
        for denom, qty in selected.items():
            total += int(denom) * int(qty)
        return total

    def _has_sufficient_vouchers(self, wallet: dict[str, int], selected: dict) -> bool:
        for denom, qty in selected.items():
            if wallet.get(str(denom), 0) < int(qty):
                return False
        return True

    def _deduct_from_household(self, household, selected: dict, total: int) -> None:
        for denom, qty in selected.items():
            denom = str(denom)
            qty = int(qty)
            if household.vouchers.get(denom, 0) < qty:
                raise ValueError("Insufficient vouchers during deduction.")
            household.vouchers[denom] -= qty

        household.balance -= int(total)
        if household.balance < 0:
            raise ValueError("Balance cannot go negative.")

    def _extract_created_time(self, txn: dict):
        value = txn.get("created_at", None)
        if value is None:
            value = txn.get("timestamp", None)
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            value = value.strip()
            # ISO format
            try:
                return datetime.fromisoformat(value)
            except Exception:
                pass
            # digits format
            try:
                return datetime.strptime(value, "%Y%m%d%H%M%S")
            except Exception:
                pass

        return None