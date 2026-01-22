import random
from models.merchant import Merchant
from storage.merchant_store import MerchantStore
from storage.bankcode_store import BankCodeStore

class MerchantService:
    """
    Business logic for merchant registration.
    Keeps an in-memory index for fast lookups and uniqueness checks.
    """

    def __init__(self, merchant_store: MerchantStore, bank_store: BankCodeStore):
        self.merchant_store = merchant_store
        self.bank_store = bank_store

        # In-memory indexes
        self.merchants_by_id: dict[str, Merchant] = {}
        self.merchants_by_uen: dict[str, Merchant] = {}

    def bootstrap_from_file(self) -> None:
        """Load existing merchants from file into memory (for restart recovery)."""
        merchants = self.merchant_store.load_all()
        for m in merchants:
            if m.merchant_id:
                self.merchants_by_id[m.merchant_id] = m
            if m.uen:
                self.merchants_by_uen[m.uen] = m

    def _generate_merchant_id(self) -> str:
        """
        Generate a unique merchant id.
        Format: M + 4 digits (e.g., M0001).
        """
        for _ in range(50):
            candidate = f"M{random.randint(0, 9999):04d}"
            if candidate not in self.merchants_by_id:
                return candidate
        raise ValueError("Unable to generate unique Merchant ID after 50 retries.")

    def register_merchant(self, payload: dict) -> Merchant:
        """
        Register a new merchant.
        """
        required = [
            "merchant_name", "uen", "bank_name", "bank_code",
            "branch_code", "account_number", "account_holder_name",
        ]
        for key in required:
            if not str(payload.get(key, "")).strip():
                raise ValueError(f"Missing required field: {key}")

        uen = payload["uen"].strip()
        bank_code = payload["bank_code"].strip()
        branch_code = payload["branch_code"].strip()

        if uen in self.merchants_by_uen:
            raise ValueError("UEN already registered.")

        if not self.bank_store.is_valid(bank_code, branch_code):
            raise ValueError("Invalid bank_code / branch_code based on BankCode.csv.")

        merchant_id = self._generate_merchant_id()
        merchant = Merchant(
            merchant_id=merchant_id,
            merchant_name=payload["merchant_name"].strip(),
            uen=uen,
            bank_name=payload["bank_name"].strip(),
            bank_code=bank_code,
            branch_code=branch_code,
            account_number=payload["account_number"].strip(),
            account_holder_name=payload["account_holder_name"].strip(),
            registration_date=Merchant.today_str(),
            status=payload.get("status", "Active").strip() or "Active",
        )

        self.merchant_store.append(merchant)
        self.merchants_by_id[merchant_id] = merchant
        self.merchants_by_uen[uen] = merchant

        return merchant

    def get_merchant(self, merchant_id: str) -> Merchant:
        """Retrieve a merchant by ID."""
        return self.merchants_by_id.get(merchant_id)