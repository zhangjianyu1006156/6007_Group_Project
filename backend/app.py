from pathlib import Path
from flask import Flask, request, jsonify

from storage.bankcode_store import BankCodeStore
from storage.merchant_store import MerchantStore
from services.merchant_service import MerchantService

def create_app() -> Flask:
    app = Flask(__name__)

    # File paths (relative to backend/)
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "storage" / "data"

    bankcode_path = data_dir / "BankCode.csv"
    merchant_path = data_dir / "Merchant.txt"

    # Initialize stores/services
    bank_store = BankCodeStore(bankcode_path)
    bank_store.load()

    merchant_store = MerchantStore(merchant_path)

    merchant_service = MerchantService(merchant_store, bank_store)
    merchant_service.bootstrap_from_file()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/merchants")
    def register_merchant():
        """
        Merchant Registration API
        Request JSON:
          merchant_name, uen, bank_name, bank_code, branch_code,
          account_number, account_holder_name, (optional) status
        Response:
          merchant_id + basic merchant info
        """
        payload = request.get_json(silent=True) or {}
        try:
            merchant = merchant_service.register_merchant(payload)
            return jsonify({
                "status": "success",
                "merchant_id": merchant.merchant_id,
                "merchant_name": merchant.merchant_name,
                "uen": merchant.uen,
                "status_value": merchant.status
            }), 201
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
