import flet as ft
import requests
import re

# Configuration
API_BASE_URL = "http://127.0.0.1:5000/api"

def main(page: ft.Page):
    page.title = "CDC Voucher App - Households"
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
        "balance": 0,
        "wallet": {},
        "selected": {}
    }

    # ==========================================
    # API CALLS
    # ==========================================
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

    # ==========================================
    # SCREENS
    # ==========================================

    # --- 1. LOGIN HOME ---
    def show_login():
        page.clean()
        h_error_text = ft.Text("", color="red", size=14)

        def login_household(e):
            h_error_text.value = "" 
            h_id = h_id_input.value
            if not h_id:
                h_error_text.value = "Please enter a Household ID"
                page.update()
                return
            
            success, data = api_check_balance(h_id)
            if success:
                state["household_id"] = h_id
                state["balance"] = data["balance"]
                state["wallet"] = data["vouchers"]
                state["selected"] = {}
                show_dashboard()
            else:
                h_error_text.value = "Invalid Household ID. Please register first."
                page.update()

        h_id_input = ft.TextField(label="Household ID", hint_text="Enter ID (e.g. H123...)")

        page.add(
            ft.Column([
                ft.Row([ft.Text("CDC Households", size=30, weight="bold", color="teal")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                
                ft.Text("Login to access vouchers", size=16),
                h_id_input,
                ft.Row([ft.Button("Login", on_click=login_household, width=360)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.TextButton("No Account? Register Household", on_click=lambda e: show_register_household())], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([h_error_text], alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    # --- 2. REGISTER HOUSEHOLD ---
    def show_register_household():
        page.clean()
        
        id_field = ft.TextField(label="Household ID (e.g. H52298800781)")
        postal_field = ft.TextField(label="Postal Code (e.g. 560456)")
        unit_field = ft.TextField(label="Unit Number (e.g. #08-02)")
        
        result_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        def handle_submit(e):
            if not re.match(r"^H\d{11}$", id_field.value):
                result_display.controls.clear()
                result_display.controls.append(ft.Text("Invalid Format. ID must start with 'H' followed by 11 digits (e.g. H52298800781)", color="red"))
                page.update()
                return

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
                                border=ft.Border.all(1, "green"),
                                border_radius=5
                            ),
                            ft.Text("(Anyone with this link can redeem vouchers)", italic=True, size=12),
                            ft.Divider(),
                            
                            ft.Button("Go to Login", on_click=lambda e: show_login())
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20, border=ft.Border.all(1, "green"), border_radius=10
                    )
                )
            else:
                result_display.controls.append(ft.Text(f"Error: {h_id}", color="red"))
            page.update()

        page.add(
            ft.Column([
                ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_login())], alignment=ft.MainAxisAlignment.START),
                
                ft.Text("Register Household", size=25, weight="bold"),
                ft.Text("Enter your details to claim vouchers."),
                
                id_field,
                postal_field,
                unit_field,
                
                ft.Row([ft.Button("Register Now", on_click=handle_submit, bgcolor="teal", color="white")], alignment=ft.MainAxisAlignment.CENTER),
                result_display
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    # --- 3. HOUSEHOLD DASHBOARD ---
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
                            bgcolor="teal", padding=10, border_radius=5, width=60, 
                            alignment=ft.Alignment(0, 0)
                        ),
                        ft.Column([
                            ft.Text(f"${denom} Voucher", weight="bold"),
                            ft.Text(f"Owned: {count}", size=12, color="grey")
                        ]),
                        ft.IconButton(ft.Icons.REMOVE, on_click=lambda e, d=denom: modify_selection(d, -1)),
                        counters[denom],
                        ft.IconButton(ft.Icons.ADD, on_click=lambda e, d=denom: modify_selection(d, 1)),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )

        total_text = ft.Text("Total Selected: $0", size=20, weight="bold", color="green")
        
        wallet_box = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("Current Balance", color="white"),
                    ft.Text(f"${state['balance']}", size=40, weight="bold", color="white"),
                    ft.Text(f"ID: {state['household_id']}", size=12, color="white70")
                ]),
                bgcolor="teal", padding=20, border_radius=10, width=400
            )
        ], alignment=ft.MainAxisAlignment.CENTER)

        generate_btn = ft.Row([
            ft.Button("Generate Code", on_click=handle_generate_code, width=400, height=50)
        ], alignment=ft.MainAxisAlignment.CENTER)

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.LOGOUT, on_click=lambda e: show_login()),
                    ft.Text("My Wallet", size=20, weight="bold"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                wallet_box,
                
                ft.Divider(),
                
                ft.Text("Select Vouchers:"),
                ft.Column(voucher_controls),
                
                ft.Divider(),
                
                ft.Row([total_text], alignment=ft.MainAxisAlignment.CENTER),
                generate_btn
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    # --- 4. CODE VIEW ---
    def show_code_view(code):
        page.clean()
        page.add(
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_dashboard()),
                ft.Container(height=50),
                ft.Text("Show to Merchant", size=20),
                ft.Container(
                    content=ft.Text(code, size=60, weight="bold"),
                    padding=30, border=ft.Border.all(2, "teal"), border_radius=10,
                    alignment=ft.Alignment(0, 0)
                ),
                ft.Text("Valid for 10 minutes", color="red", italic=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
        )
        page.update()

    show_login()

if __name__ == "__main__":
    ft.run(main)