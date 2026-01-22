from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import string
from typing import Dict, List, Tuple

from server.models.voucher import Voucher
from server.models.reservation import Reservation
from server.storage.memory_store import MemoryStore

UTC = timezone.utc

def now_utc() -> datetime:
    return datetime.now(UTC)

class EnquiryService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        if not self.store.vouchers:
            self.seed_demo_household(household_id="H1", entitlement=800)

    def seed_demo_household(self, household_id: str, entitlement: int = 800) -> None:
        """Seed demo vouchers totalling `entitlement` for one household.
        This is ONLY for demo/testing before Registration module is integrated.
        """
        plan = [(10, 60), (5, 20), (2, 50)]
        total = sum(denom * cnt for denom, cnt in plan)
        if total != entitlement:
            plan = [(10, entitlement // 10)]
        i = 1
        for denom, cnt in plan:
            for _ in range(cnt):
                vid = f"V{household_id}-{i:04d}"
                self.store.vouchers[vid] = Voucher(
                    voucher_id=vid,
                    household_id=household_id,
                    denomination=denom,
                    state="AVAILABLE",
                )
                i += 1

    def _gen_redemption_number(self, length: int = 10) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def cleanup_expired(self) -> None:
        t = now_utc()
        for rn, res in list(self.store.reservations.items()):
            if res.status == "ACTIVE" and t >= res.expires_at:
                res.status = "EXPIRED"
                for vid in res.voucher_ids:
                    v = self.store.vouchers.get(vid)
                    if v and v.state == "RESERVED":
                        v.state = "AVAILABLE"
                        v.reserved_until = None

    def get_balance(self, household_id: str) -> Tuple[int, Dict[int, int]]:
        self.cleanup_expired()
        total = 0
        breakdown: Dict[int, int] = {}
        for v in self.store.vouchers.values():
            if v.household_id == household_id and v.state == "AVAILABLE":
                total += v.denomination
                breakdown[v.denomination] = breakdown.get(v.denomination, 0) + 1
        return total, breakdown

    def list_available_vouchers(self, household_id: str) -> List[Voucher]:
        self.cleanup_expired()
        vs = [
            v for v in self.store.vouchers.values()
            if v.household_id == household_id and v.state == "AVAILABLE"
        ]
        vs.sort(key=lambda x: (-x.denomination, x.voucher_id))
        return vs

    def create_redemption_code_for_selection(
        self,
        household_id: str,
        voucher_ids: List[str],
        ttl_seconds: int = 300,
    ) -> Reservation:
        """Lock selected vouchers (temporary) and return a redemption number.
        Redemption/deduction is done by the Redemption module later.
        """
        self.cleanup_expired()

        if not voucher_ids:
            raise ValueError("No vouchers selected")

        seen = set()
        clean_ids: List[str] = []
        for vid in voucher_ids:
            if vid in seen:
                continue
            seen.add(vid)
            clean_ids.append(vid)

        amount = 0
        for vid in clean_ids:
            v = self.store.vouchers.get(vid)
            if not v:
                raise ValueError(f"Invalid voucher: {vid}")
            if v.household_id != household_id:
                raise ValueError("Selected voucher does not belong to this household")
            if v.state != "AVAILABLE":
                raise ValueError("Selected voucher is not available (already reserved/redeemed)")
            amount += v.denomination

        rn = self._gen_redemption_number()
        while rn in self.store.reservations:
            rn = self._gen_redemption_number()

        created = now_utc()
        expires = created + timedelta(seconds=ttl_seconds)

        for vid in clean_ids:
            v = self.store.vouchers[vid]
            v.state = "RESERVED"
            v.reserved_until = expires

        res = Reservation(
            redemption_number=rn,
            household_id=household_id,
            voucher_ids=clean_ids,
            amount=amount,
            created_at=created,
            expires_at=expires,
            status="ACTIVE",
        )
        self.store.reservations[rn] = res
        return res
