import flet as ft
import requests

# Configuration
API_BASE_URL = "http://127.0.0.1:5000/api"

def main(page: ft.Page):
    page.title = "CDC Voucher App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.padding = 20
    page.scroll = "auto"

    # ==========================================
    # STATE
    # ==========================================
    state = {
        "household_id": "",
        "merchant_id": "",
        "balance": 0,
        "wallet": {},
        "selected": {}
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
            # Check if merchant exists
            resp = requests.get(f"{API_BASE_URL}/merchants/{m_id}")
            if resp.status_code == 200:
                return True, resp.json()
            return False, "Invalid Merchant ID"
        except Exception as e:
            return False, str(e)

    def api_register_household(h_id, postal, unit):
        data = {
            "household_id": h_id,
            "postal_code": postal,
            "unit_number": unit
        }
        try:
            resp = requests.post(f"{API_BASE_URL}/households", json=data)
            if resp.status_code == 201:
                data = resp.json()
                link = data.get("link", "")
                created_id = link.split("/")[-1] if link else h_id
                return True, created_id, link
            return False, resp.json().get("error", "Registration failed"), None
        except Exception as e:
            return False, str(e), None

    def api_check_balance(h_id):
        try:
            resp = requests.post(f"{API_BASE_URL}/enquiry", json={
                "household_id": h_id, 
                "action": "check_balance"
            })
            if resp.status_code == 200:
                return True, resp.json()
            return False, resp.json().get("error", "Login failed")
        except Exception as e:
            return False, str(e)

    def api_generate_code(h_id, selected_vouchers):
        try:
            resp = requests.post(f"{API_BASE_URL}/enquiry", json={
                "household_id": h_id,
                "action": "generate_code",
                "vouchers": selected_vouchers
            })
            if resp.status_code == 200:
                return True, resp.json().get("code")
            return False, resp.json().get("error", "Error generating code")
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

    # --- 1. LOGIN HOME ---
    def show_login():
        page.clean()

        def login_household(e):
            h_id = h_id_input.value
            if not h_id: return
            success, data = api_check_balance(h_id)
            if success:
                state["household_id"] = h_id
                state["balance"] = data["balance"]
                state["wallet"] = data["vouchers"]
                state["selected"] = {}
                show_dashboard()
            else:
                # Show Error Message
                page.snack_bar = ft.SnackBar(ft.Text("Invalid Household ID. Please register first."), bgcolor=ft.Colors.RED_400)
                page.snack_bar.open = True
                page.update()

        def login_merchant(e):
            m_id = m_id_input.value
            if not m_id: return
            
            # Verify Merchant Exists
            success, data = api_verify_merchant(m_id)
            if success:
                state["merchant_id"] = m_id
                show_merchant_view()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Invalid Merchant ID."), bgcolor=ft.Colors.RED_400)
                page.snack_bar.open = True
                page.update()

        h_id_input = ft.TextField(label="Household ID", hint_text="Enter ID (e.g. H123...)")
        m_id_input = ft.TextField(label="Merchant ID", hint_text="Enter ID (e.g. M000...)")

        page.add(
            ft.Column([
                ft.Text("CDC Voucher App", size=30, weight="bold", color="teal"),
                ft.Divider(),
                
                # Household Section
                ft.Text("Residents", size=20, weight="bold"),
                h_id_input,
                ft.ElevatedButton("Login", on_click=login_household, width=360),
                ft.TextButton("No Account? Register Household", on_click=lambda e: show_register_household()),
                
                ft.Divider(),
                
                # Merchant Section
                ft.Text("Merchants", size=20, weight="bold"),
                m_id_input,
                ft.ElevatedButton("Login", on_click=login_merchant, width=360),
                ft.TextButton("New Business? Register Merchant", on_click=lambda e: show_register_merchant()),
            ], spacing=15)
        )
        page.update()

    # --- 2. REGISTER HOUSEHOLD ---
    def show_register_household():
        page.clean()
        
        id_field = ft.TextField(label="Household ID (e.g. H123456)")
        postal_field = ft.TextField(label="Postal Code (e.g. 123456)")
        unit_field = ft.TextField(label="Unit Number (e.g. #06-03)")
        
        result_display = ft.Column()

        def handle_submit(e):
            success, h_id, link = api_register_household(
                id_field.value,
                postal_field.value,
                unit_field.value
            )
            result_display.controls.clear()
            if success:
                result_display.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=50),
                            ft.Text("Registration Successful!", color="green", weight="bold"),
                            
                            ft.Divider(),
                            ft.Text("Share this link with your family:", size=16),
                            ft.Container(
                                content=ft.Text(link, color="blue", size=18, weight="bold", selectable=True),
                                padding=10,
                                bgcolor=ft.Colors.BLUE_50,
                                border_radius=5
                            ),
                            ft.Text("(Anyone with this link can redeem vouchers)", italic=True, size=12),
                            ft.Divider(),
                            
                            ft.ElevatedButton("Go to Login", on_click=lambda e: show_login())
                        ], horizontal_alignment="center"),
                        padding=20, border=ft.border.all(1, "green"), border_radius=10
                    )
                )
            else:
                result_display.controls.append(ft.Text(f"Error: {h_id}", color="red"))
            page.update()

        page.add(
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_login()),
                ft.Text("Register Household", size=25, weight="bold"),
                ft.Text("Enter your details to claim vouchers."),
                id_field,
                postal_field,
                unit_field,
                ft.ElevatedButton("Register Now", on_click=handle_submit, bgcolor="teal", color="white"),
                result_display
            ])
        )
        page.update()

    # --- 3. REGISTER MERCHANT ---
    def show_register_merchant():
        page.clean()

        name = ft.TextField(label="Business Name")
        uen = ft.TextField(label="UEN (Business Reg No)")
        
        bank_name = ft.Dropdown(label="Bank Name", options=[
            ft.dropdown.Option("DBS Bank Ltd"),
            ft.dropdown.Option("OCBC Bank"),
            ft.dropdown.Option("UOB Bank"),
        ])
        
        bank_code = ft.TextField(label="Bank Code", hint_text="e.g. 7171", expand=True)
        branch_code = ft.TextField(label="Branch Code", hint_text="e.g. 001", expand=True)
        acc_num = ft.TextField(label="Account Number")
        holder = ft.TextField(label="Account Holder Name")

        result_display = ft.Column()

        def handle_submit(e):
            data = {
                "merchant_name": name.value,
                "uen": uen.value,
                "bank_name": bank_name.value,
                "bank_code": bank_code.value,
                "branch_code": branch_code.value,
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
                            ft.ElevatedButton("Go to Login", on_click=lambda e: show_login())
                        ], horizontal_alignment="center"),
                        padding=20, border=ft.border.all(1, "blue"), border_radius=10
                    )
                )
            else:
                result_display.controls.append(ft.Text(f"Error: {res}", color="red"))
            page.update()

        page.add(
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_login()),
                ft.Text("Merchant Sign-Up", size=25, weight="bold"),
                name, uen, bank_name,
                ft.Row([bank_code, branch_code]),
                acc_num, holder,
                ft.ElevatedButton("Submit Registration", on_click=handle_submit, bgcolor="blue", color="white"),
                result_display
            ])
        )
        page.update()

    # --- 4. HOUSEHOLD DASHBOARD ---
    def show_dashboard():
        page.clean()
        
        def update_selection_display():
            total = 0
            for denom, qty in state["selected"].items():
                total += int(denom) * qty
            total_text.value = f"Total Selected: ${total}"
            page.update()

        def modify_selection(denom, delta):
            current_qty = state["selected"].get(denom, 0)
            max_qty = state["wallet"].get(denom, 0)
            new_qty = current_qty + delta
            if 0 <= new_qty <= max_qty:
                state["selected"][denom] = new_qty
                counters[denom].value = str(new_qty)
                update_selection_display()

        def handle_generate_code(e):
            final_vouchers = {k: v for k, v in state["selected"].items() if v > 0}
            if not final_vouchers:
                page.snack_bar = ft.SnackBar(ft.Text("Select at least one voucher!"))
                page.snack_bar.open = True
                page.update()
                return

            success, result = api_generate_code(state["household_id"], final_vouchers)
            if success:
                show_code_view(result)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error: {result}"))
                page.snack_bar.open = True
                page.update()

        # Build UI
        voucher_controls = []
        counters = {}
        sorted_denoms = sorted(state["wallet"].keys(), key=lambda x: int(x))

        for denom in sorted_denoms:
            count = state["wallet"][denom]
            if count > 0:
                counters[denom] = ft.Text("0", size=20, width=30, text_align="center")
                voucher_controls.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"${denom}", color="white", weight="bold"),
                            bgcolor="teal", padding=10, border_radius=5, width=60, alignment=ft.alignment.center
                        ),
                        ft.Column([
                            ft.Text(f"${denom} Voucher", weight="bold"),
                            ft.Text(f"Owned: {count}", size=12, color="grey")
                        ]),
                        ft.IconButton(ft.Icons.REMOVE, on_click=lambda e, d=denom: modify_selection(d, -1)),
                        counters[denom],
                        ft.IconButton(ft.Icons.ADD, on_click=lambda e, d=denom: modify_selection(d, 1)),
                    ], alignment="spaceBetween")
                )

        total_text = ft.Text("Total Selected: $0", size=20, weight="bold", color="green")

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.LOGOUT, on_click=lambda e: show_login()),
                    ft.Text("My Wallet", size=20, weight="bold"),
                ], alignment="spaceBetween"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Current Balance", color="white"),
                        ft.Text(f"${state['balance']}", size=40, weight="bold", color="white"),
                        ft.Text(f"ID: {state['household_id']}", size=12, color="white70")
                    ]),
                    bgcolor="teal", padding=20, border_radius=10, width=400
                ),
                ft.Divider(),
                ft.Text("Select Vouchers:"),
                ft.Column(voucher_controls),
                ft.Divider(),
                ft.Row([total_text], alignment="center"),
                ft.ElevatedButton("Generate Code", on_click=handle_generate_code, width=400, height=50)
            ])
        )
        page.update()

    # --- 5. CODE VIEW ---
    def show_code_view(code):
        page.clean()
        page.add(
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_dashboard()),
                ft.Container(height=50),
                ft.Text("Show to Merchant", size=20),
                ft.Container(
                    content=ft.Text(code, size=60, weight="bold"),
                    padding=30, border=ft.border.all(2, "teal"), border_radius=10,
                    alignment=ft.alignment.center
                ),
                ft.Text("Valid for 10 minutes", color="red", italic=True),
            ], horizontal_alignment="center", alignment="center")
        )
        page.update()

    # --- 6. MERCHANT DASHBOARD ---
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

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.LOGOUT, on_click=lambda e: show_login()),
                    ft.Text(f"Merchant: {state['merchant_id']}", size=16, weight="bold"),
                ], alignment="spaceBetween"),
                ft.Divider(),
                ft.Text("Scan Code", size=20),
                code_input,
                ft.ElevatedButton("Redeem", on_click=handle_redeem, width=400, height=50, bgcolor="orange", color="white"),
                ft.Container(
                    content=result_text,
                    padding=20,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=10,
                    width=400
                )
            ], horizontal_alignment="center")
        )
        page.update()

    show_login()

if __name__ == "__main__":
    ft.app(target=main)