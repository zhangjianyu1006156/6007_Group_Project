from typing import Dict
from server.models.voucher import Voucher
from server.models.reservation import Reservation

class MemoryStore:
    def __init__(self) -> None:
        self.vouchers: Dict[str, Voucher] = {}
        self.reservations: Dict[str, Reservation] = {}
