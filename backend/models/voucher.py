from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Voucher:
    voucher_id: str
    household_id: str
    denomination: int
    state: str = "AVAILABLE"
    reserved_until: Optional[datetime] = None
