from pathlib import Path
from flask import Flask, request, jsonify

# Imports
from storage.bankcode_store import BankCodeStore
from storage.merchant_store import MerchantStore
from storage.household_store import HouseholdStore
from storage.redemption_store import RedemptionStore
from storage.counter_store import CounterStore

from services.merchant_service import MerchantService
from services.household_service import HouseholdService
from services.redemption_service import RedemptionService

def create_app() -> Flask:
    app = Flask(__name__)

    # Paths
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "storage" / "data"
    
    # Initialize Stores
    bank_store = BankCodeStore(data_dir / "BankCode.csv")
    bank_store.load()
    merchant_store = MerchantStore(data_dir / "Merchant.txt")
    household_store = HouseholdStore(data_dir / "households.json")
    counter_store = CounterStore(data_dir / "counters.json")
    redemption_store = RedemptionStore(data_dir)

    # Initialize Services
    merchant_service = MerchantService(merchant_store, bank_store)
    merchant_service.bootstrap_from_file()

    household_service = HouseholdService(household_store)
    household_service.bootstrap_from_file()
    
    # Shared memory for pending codes
    pending_codes_memory = {}
    
    # Initialize Redemption Service
    redemption_service = RedemptionService(
        household_service=household_service,
        household_store=household_store,
        merchant_service=merchant_service,
        counter_store=counter_store,       
        redemption_store=redemption_store, 
        pending_codes=pending_codes_memory,
        code_ttl_seconds=600
    )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # --- 1. MERCHANT REGISTRATION & VERIFICATION ---
    @app.post("/api/merchants")
    def register_merchant():
        payload = request.get_json(silent=True) or {}
        try:
            merchant = merchant_service.register_merchant(payload)
            return jsonify({"status": "success", "merchant_id": merchant.merchant_id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/merchants/<merchant_id>")
    def check_merchant(merchant_id):
        merchant = merchant_service.get_merchant(merchant_id)
        if merchant:
            return jsonify({"status": "exists", "name": merchant.merchant_name})
        return jsonify({"error": "Merchant not found"}), 404

    # --- 2. HOUSEHOLD REGISTRATION ---
    @app.post("/api/households")
    def register_household():
        payload = request.get_json(silent=True) or {}
        
        # Get all fields
        h_id = payload.get("household_id")
        postal = payload.get("postal_code")
        unit = payload.get("unit_number")

        try:
            household = household_service.register_household(
                household_id=h_id,
                postal_code=postal,
                unit_number=unit
            )
            return jsonify({"status": "success", "link": household.link}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    # --- 3. ENQUIRY (Check Balance & Generate Code) ---
    @app.post("/api/enquiry")
    def enquiry():
        payload = request.get_json(silent=True) or {}
        h_id = payload.get("household_id")
        action = payload.get("action") 

        if not h_id:
            return jsonify({"error": "Missing household_id"}), 400
        
        try:
            if action == "generate_code":
                vouchers = payload.get("vouchers")
                if not vouchers:
                    return jsonify({"error": "No vouchers provided"}), 400
                
                code = redemption_service.generate_code(h_id, vouchers)
                return jsonify({"status": "success", "code": code})
            
            else: 
                household = household_service.get_household(h_id)
                if not household:
                    return jsonify({"error": "Not found"}), 404
                
                return jsonify({
                    "status": "success", 
                    "balance": household.balance,
                    "vouchers": household.vouchers
                })

        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    # --- 4. REDEMPTION (Merchant Claims Code) ---
    @app.post("/api/redemption")
    def redeem():
        payload = request.get_json(silent=True) or {}
        try:
            result = redemption_service.redeem(
                code=payload.get("code"),
                merchant_id=payload.get("merchant_id")
            )
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)