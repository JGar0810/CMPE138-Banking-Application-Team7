# SJSU CMPE 138 SPRING 2026 TEAM7


import bcrypt
from app.db import get_connection
from app.logger import log_action, log_error
from app.ahmad_ops import AhmadBankingService


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def ask_int(prompt: str, allow_blank: bool = False):
    while True:
        raw = input(prompt).strip()
        if allow_blank and raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Please enter a whole number.")

def ask_amount(prompt: str, allow_zero: bool = False):
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value < 0 or (not allow_zero and value == 0):
                raise ValueError
            return raw
        except ValueError:
            extra = " or 0" if allow_zero else ""
            print(f"Please enter a positive number{extra}.")

def print_result(result):
    print("\nSUCCESS" if result.ok else "\nERROR")
    print(result.message)
    if result.payload:
        for k, v in result.payload.items():
            print(f"  {k}: {v}")
    print()
# ----------------------------
# LOGIN
# ----------------------------
def login():
    print("\n=== Welcome to Team7 Banking System ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check Employee table first
        cursor.execute("SELECT *, 'employee' as user_type FROM Employee WHERE login_id = %s", (username,))
        user = cursor.fetchone()

        # If not found, check Customer table
        if not user:
            cursor.execute("SELECT *, 'customer' as user_type FROM Customer WHERE username = %s", (username,))
            user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            log_action(username, "LOGIN", "Success")
            role = user.get('role', 'customer')
            print(f"\nWelcome, {user['first_name']}! Role: {role}")
            return user
        else:
            log_error(username, "LOGIN", "Invalid credentials")
            print("Invalid username or password.")
            return None

    except Exception as e:
        log_error(username, "LOGIN", str(e))
        print(f"Database error: {e}")
        return None

# ----------------------------
# MENUS
# ----------------------------
def customer_menu(user):
    while True:
        print("\n--- Customer Menu ---")
        print("1. View Accounts")
        print("2. View Transactions")
        print("3. Update Profile")
        print("4. Apply for Loan")
        print("5. View Loan Status")
        print("6. Make Loan Payment")
        print("7. Request Card")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            pass  # Evan fills this in
        elif choice == "2":
            pass  # Evan fills this in
        elif choice == "3":
            pass  # Evan fills this in
        elif choice == "4":
            pass  # Evan fills this in
        elif choice == "5":
            pass  # Evan fills this in
        elif choice == "6":
            pass  # Evan fills this in
        elif choice == "7":
            pass  # Ahmad fills this in
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")

def teller_menu(user):
    conn = get_connection()
    service = AhmadBankingService(conn)
    while True:
        print("\n--- Teller Menu ---")
        print("1. Process Deposit")
        print("2. Process Withdrawal")
        print("3. Open Account")
        print("4. Close Account")
        print("5. Fund Transfer")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            account_id = ask_int("Account ID: ")
            amount = ask_amount("Deposit amount: ")
            teller_id = user["employee_id"]
            description = input("Description [CLI deposit]: ").strip() or "CLI deposit"
            result = service.process_deposit(account_id, amount, teller_id, description)
            print_result(result)
        elif choice == "2":
            account_id = ask_int("Account ID: ")
            amount = ask_amount("Withdrawal amount: ")
            teller_id = user["employee_id"]
            description = input("Description [CLI withdrawal]: ").strip() or "CLI withdrawal"
            result = service.process_withdrawal(account_id, amount, teller_id, description)
            print_result(result)
        elif choice == "3":
            customer_id = ask_int("Customer ID: ")
            account_type = input("Account type (checking/savings): ").strip().lower()
            opening_deposit = ask_amount("Opening deposit (0 allowed): ", allow_zero=True)
            result = service.open_account(customer_id, account_type, opening_deposit, user["employee_id"])
            print_result(result)
        elif choice == "4":
            account_id = ask_int("Account ID: ")
            result = service.close_account(account_id)
            print_result(result)
        elif choice == "5":
            transfer_funds(user)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")
    conn.close()

def loan_officer_menu(user):
    while True:
        print("\n--- Loan Officer Menu ---")
        print("1. Review Loan Applications")
        print("2. Approve Loan")
        print("3. Reject Loan")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            pass  # Ahmad fills this in
        elif choice == "2":
            pass  # Ahmad fills this in
        elif choice == "3":
            pass  # Ahmad fills this in
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")

def manager_menu(user):
    while True:
        print("\n--- Manager Menu ---")
        print("1. Process Deposit")
        print("2. Process Withdrawal")
        print("3. Open Account")
        print("4. Close Account")
        print("5. Fund Transfer")
        print("6. Review Loan Applications")
        print("7. Approve Loan")
        print("8. Reject Loan")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            pass  # Ahmad fills this in
        elif choice == "2":
            pass  # Ahmad fills this in
        elif choice == "3":
            pass  # Ahmad fills this in
        elif choice == "4":
            pass  # Ahmad fills this in
        elif choice == "5":
            transfer_funds(user)
        elif choice == "6":
            pass  # Ahmad fills this in
        elif choice == "7":
            pass  # Ahmad fills this in
        elif choice == "8":
            pass  # Ahmad fills this in
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")

# ----------------------------
# FUND TRANSFER (Jose - Day 2)
# ----------------------------
def transfer_funds(user):
    print("\n--- Fund Transfer ---")
    try:
        from_account = input("From Account ID: ").strip()
        to_account = input("To Account ID: ").strip()
        amount = float(input("Amount: $").strip())

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify from account exists and has enough balance
        cursor.execute("SELECT * FROM Account WHERE account_id = %s AND status = 'active'", (from_account,))
        source = cursor.fetchone()

        if not source:
            print("Source account not found or inactive.")
            return

        if source["balance"] < amount:
            print("Insufficient funds.")
            return

        # Verify to account exists
        cursor.execute("SELECT * FROM Account WHERE account_id = %s AND status = 'active'", (to_account,))
        destination = cursor.fetchone()

        if not destination:
            print("Destination account not found or inactive.")
            return

        # Execute transfer as a transaction
        conn.start_transaction()

        cursor.execute("UPDATE Account SET balance = balance - %s WHERE account_id = %s", (amount, from_account))
        cursor.execute("UPDATE Account SET balance = balance + %s WHERE account_id = %s", (amount, to_account))

        cursor.execute("""
            INSERT INTO `Transaction` (account_id, transaction_type, amount, description, processed_by)
            VALUES (%s, 'transfer_out', %s, %s, %s)
        """, (from_account, amount, f"Transfer to account {to_account}", user["employee_id"]))

        cursor.execute("""
            INSERT INTO `Transaction` (account_id, transaction_type, amount, description, processed_by)
            VALUES (%s, 'transfer_in', %s, %s, %s)
        """, (to_account, amount, f"Transfer from account {from_account}", user["employee_id"]))

        conn.commit()
        log_action(user["login_id"], "TRANSFER", f"${amount} from account {from_account} to {to_account}")
        print(f"\nTransfer of ${amount:.2f} successful!")

    except Exception as e:
        conn.rollback()
        log_error(user.get("login_id", "unknown"), "TRANSFER", str(e))
        print(f"Transfer failed: {e}")

    finally:
        cursor.close()
        conn.close()

# ----------------------------
# MAIN
# ----------------------------
def main():
    while True:
        user = login()
        if not user:
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != "y":
                print("Goodbye.")
                break
            continue

        role = user.get("role", "customer").lower()
        user_type = user.get("user_type", "")

        if user_type == "customer":
            customer_menu(user)
        elif role == "teller":
            teller_menu(user)
        elif role == "loan_officer":
            loan_officer_menu(user)
        elif role == "manager":
            manager_menu(user)
        else:
            print(f"Unknown role: {role}. Contact admin.")

        # After logout, loop back to login
        print("\nSession ended.")

if __name__ == "__main__":
    main()
