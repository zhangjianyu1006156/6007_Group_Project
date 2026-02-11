---

# CDC Voucher System

---

## 1. System Requirements

* Python 3.10 or above
* pip (Python package manager)

Install dependencies:

```bash
pip install flask requests
pip install flet==0.8.3
```

Important:
This project is developed and tested with Flet 0.8.3.
Using other versions may cause the application to fail or not run properly.
---

## 2. Project Structure

```
backend/
│── app.py                # Flask API server
│── models/               # Data models
│── services/             # Business logic
│── storage/              # File-based persistence
│    └── data/            # CSV / JSON data files

household_frontend.py     # Household UI
merchant_frontend.py      # Merchant UI
```

---

## 3. How to Run the System

### Step 1 – Start Backend

```bash
cd backend
python app.py
```

### Step 2 – Start Frontend Applications (in separate terminals)

```bash
python household_frontend.py
python merchant_frontend.py
```

Both applications connect to the same backend API at `http://127.0.0.1:5000`.

---

## 4. System Persistence

The system uses **file-based storage (CSV / JSON)**:

* `households.json` → Household records
* `Merchant.txt` → Merchant records
* `RedeemYYYYMMDD.csv` → Redemption logs
* `counters.json` → Code counters

When the server restarts:

* Data is automatically reloaded during initialization
* The system resumes from its previous state
* No data is lost

---

## 5. Key Design Features

* Clear separation: Model / Service / Store
* Strict input validation (e.g., Household ID: H + 11 digits)
* API-driven architecture
* Restart recovery supported via persistent files

---

This implementation demonstrates a structured backend design with reliable data persistence suitable for the project scope.

---
