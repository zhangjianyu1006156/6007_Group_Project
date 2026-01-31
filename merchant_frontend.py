import flet as ft
import requests
import csv
import os

API_BASE_URL = "http://127.0.0.1:5000/api"

def main(page: ft.Page):
    page.title = "CDC Voucher App - Merchants"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.padding = 20
    page.scroll = "auto"

    state = {
        "merchant_id": "",
        "banks": {} 
    }

    # ==========================================
    # API CALLS
    # ==========================================
    def api_register_merchant(data):
        try:
            resp = requests.post(f"{API_BASE_URL}/merchants", json=data)
            if resp.status_code == 201:
                return True, resp.json()
            return False, resp.json().get("error", "Registration failed")
        except Exception as e:
            return False, str(e)

    def api_verify_merchant(m_id):
        try:
            resp = requests.get(f"{API_BASE_URL}/merchants/{m_id}")
            if resp.status_code == 200:
                return True, resp.json()
            return False, "Invalid Merchant ID"
        except Exception as e:
            return False, str(e)

    def api_redeem(m_id, code):
        try:
            resp = requests.post(f"{API_BASE_URL}/redemption", json={
                "merchant_id": m_id, 
                "code": code
            })
            if resp.status_code == 200:
                return True, resp.json()
            return False, resp.json().get("error", "Redemption failed")
        except Exception as e:
            return False, str(e)

    # ==========================================
    # SCREENS
    # ==========================================

    def show_login():
        page.clean()
        m_error_text = ft.Text("", color="red", size=14)

        def login_merchant(e):
            m_error_text.value = ""
            if not m_id_input.value:
                m_error_text.value = "Please enter a Merchant ID"
                page.update()
                return
            
            success, data = api_verify_merchant(m_id_input.value)
            if success:
                state["merchant_id"] = m_id_input.value
                show_merchant_view()
            else:
                m_error_text.value = "Invalid Merchant ID."
                page.update()

        m_id_input = ft.TextField(label="Merchant ID", hint_text="Enter ID (e.g. M000...)")

        page.add(
            ft.Column([
                ft.Row([ft.Text("CDC Merchants", size=30, weight="bold", color="teal")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("Login to redeem vouchers", size=16),
                m_id_input,
                ft.Row([ft.Button("Login", on_click=login_merchant, width=360)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.TextButton("New Business? Register Merchant", on_click=lambda e: show_register_merchant())], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([m_error_text], alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    def show_register_merchant():
        page.clean()

        # Only load if we haven't already
        if not state["banks"]:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, "backend", "storage", "data", "BankCode.csv")
            
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if "Bank_Name" in row:
                                state["banks"][row["Bank_Name"]] = {
                                    "code": row["Bank_Code"],
                                    "branch": row["Branch_Code"]
                                }
                except Exception:
                    pass 

        name = ft.TextField(label="Business Name")
        uen = ft.TextField(label="UEN (Business Reg No)")
        
        bank_items = [ft.dropdown.Option(b) for b in state["banks"].keys()]
        
        bank_name_dropdown = ft.Dropdown(
            label="Bank Name", 
            options=bank_items
        )
        
        acc_num = ft.TextField(label="Account Number")
        holder = ft.TextField(label="Account Holder Name")

        result_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        def handle_submit(e):
            if not (uen.value.isdigit() and len(uen.value) in [9, 10]):
                result_display.controls.clear()
                result_display.controls.append(ft.Text("UEN must be 9 or 10 digits", color="red"))
                page.update()
                return

            selected_bank = bank_name_dropdown.value
            if not selected_bank or selected_bank not in state["banks"]:
                 result_display.controls.clear()
                 result_display.controls.append(ft.Text("Please select a valid bank.", color="red"))
                 page.update()
                 return
            
            # Lookup codes silently
            bank_info = state["banks"][selected_bank]
            hidden_bank_code = bank_info["code"]
            hidden_branch_code = bank_info["branch"]

            data = {
                "merchant_name": name.value,
                "uen": uen.value,
                "bank_name": selected_bank,
                "bank_code": hidden_bank_code,
                "branch_code": hidden_branch_code,
                "account_number": acc_num.value,
                "account_holder_name": holder.value
            }
            
            success, res = api_register_merchant(data)
            result_display.controls.clear()
            
            if success:
                m_id = res.get("merchant_id")
                result_display.controls.append(
                     ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.STORE, color="blue", size=50),
                            ft.Text("Welcome Aboard!", color="blue", weight="bold"),
                            ft.Text("Your Merchant ID is:", size=16),
                            ft.Text(m_id, size=40, weight="bold", selectable=True),
                            ft.Button("Go to Login", on_click=lambda e: show_login())
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20, border=ft.Border.all(1, "blue"), border_radius=10
                    )
                )
            else:
                result_display.controls.append(ft.Text(f"Error: {res}", color="red"))
            page.update()

        page.add(
            ft.Column([
                ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_login())], alignment=ft.MainAxisAlignment.START),
                ft.Text("Merchant Sign-Up", size=25, weight="bold"),
                name, uen, bank_name_dropdown,
                acc_num, holder,
                ft.Row([ft.Button("Register Now", on_click=handle_submit, bgcolor="teal", color="white")], alignment=ft.MainAxisAlignment.CENTER),
                result_display
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    def show_merchant_view():
        page.clean()
        code_input = ft.TextField(label="Voucher Code", text_align="center", text_size=24)
        result_text = ft.Text("", size=16)

        def handle_redeem(e):
            success, res = api_redeem(state["merchant_id"], code_input.value)
            if success:
                result_text.value = f"Success!\nTX: {res['transaction_id']}\nAmount: ${res['amount_redeemed']}"
                result_text.color = "green"
                code_input.value = ""
            else:
                result_text.value = f"Failed: {res}"
                result_text.color = "red"
            page.update()

        action_area = ft.Column([
            ft.Text("Scan Code", size=20),
            code_input,
            ft.Button("Redeem", on_click=handle_redeem, width=400, height=50, bgcolor="orange", color="white"),
            ft.Container(
                content=result_text,
                padding=20,
                bgcolor=ft.Colors.GREY_100,
                border_radius=10,
                width=400
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.LOGOUT, on_click=lambda e: show_login()),
                    ft.Text(f"Merchant: {state['merchant_id']}", size=16, weight="bold"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                action_area
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    show_login()

if __name__ == "__main__":
    ft.run(main)