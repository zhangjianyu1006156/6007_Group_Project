from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Reservation:
    redemption_number: str
    household_id: str
    voucher_ids: List[str]
    amount: int
    created_at: datetime
    expires_at: datetime
    status: str = "ACTIVE" 
