# SJSU CMPE 138 SPRING 2026 TEAM7

<<<<<<< HEAD
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv
from logger import log_action, log_error

load_dotenv()

# ----------------------------
# DB CONNECTION
# ----------------------------
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "banking_user"),
        password=os.getenv("DB_PASSWORD", "banking_pass"),
        database=os.getenv("DB_NAME", "banking_system")
    )

=======

import bcrypt
from app.db import get_connection
from app.logger import log_action, log_error
from app.ahmad_ops import AhmadBankingService
from app.evan_ops import EvanBankingService


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

def print_rows(title, rows):
    if not rows:
        print(f"\nNo {title.lower()} found.")
        return
    print(f"\n--- {title} ---")
    for row in rows:
        print()
        for k, v in row.items():
            print(f"  {k}: {v}")
    print()
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
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
<<<<<<< HEAD
=======
    conn = get_connection()
    service = EvanBankingService(conn)

>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
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
<<<<<<< HEAD
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
=======
            result = service.view_accounts(user["customer_id"])
            if result["ok"]:
                print_rows("Accounts", result["rows"])
            else:
                print("\nERROR")
                print(result["message"])
                print()
        elif choice == "2":
            result = service.view_transactions(user["customer_id"])
            if result["ok"]:
                print_rows("Transactions", result["rows"])
            else:
                print("\nERROR")
                print(result["message"])
                print()
        elif choice == "3":
            print("\nLeave blank if you do not want to change a field.")
            address = input("New address: ").strip()
            phone = input("New phone: ").strip()
            email = input("New email: ").strip()

            result = service.update_profile(
                user["customer_id"],
                address=address or None,
                phone=phone or None,
                email=email or None,
            )
            if result["ok"]:
                print("\nSUCCESS")
                print(result["message"])
                print()
            else:
                print("\nERROR")
                print(result["message"])
                print()
        elif choice == "4":
            loan_amount = input("Loan amount: ").strip()
            interest_rate = input("Interest rate (%): ").strip()
            loan_term_months = input("Loan term in months: ").strip()

            result = service.apply_for_loan(
                user["customer_id"],
                loan_amount,
                interest_rate,
                loan_term_months
            )
            if result["ok"]:
                print("\nSUCCESS")
                print(result["message"])
                print(f"Loan ID: {result['loan_id']}")
                print(f"Monthly Payment: {result['monthly_payment']}")
                print()
            else:
                print("\nERROR")
                print(result["message"])
                print()
        elif choice == "5":
            result = service.view_loan_status(user["customer_id"])
            if result["ok"]:
                print_rows("Loans", result["rows"])
            else:
                print("\nERROR")
                print(result["message"])
                print()
        elif choice == "6":
            loan_id = input("Loan ID: ").strip()
            amount = input("Payment amount: ").strip()

            result = service.make_loan_payment(
                user["customer_id"],
                loan_id,
                amount
            )
            if result["ok"]:
                print("\nSUCCESS")
                print(result["message"])
                print(f"Paid Amount: {result['paid_amount']}")
                print(f"Remaining Balance: {result['remaining_balance']}")
                print(f"Loan Status: {result['loan_status']}")
                print()
            else:
                print("\nERROR")
                print(result["message"])
                print()
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
        elif choice == "7":
            pass  # Ahmad fills this in
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")
<<<<<<< HEAD

def teller_menu(user):
=======
    
    conn.close()

def teller_menu(user):
    conn = get_connection()
    service = AhmadBankingService(conn)
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
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
<<<<<<< HEAD
            pass  # Ahmad fills this in
        elif choice == "2":
            pass  # Ahmad fills this in
        elif choice == "3":
            pass  # Ahmad fills this in
        elif choice == "4":
            pass  # Ahmad fills this in
=======
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
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
        elif choice == "5":
            transfer_funds(user)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")
<<<<<<< HEAD
=======
    conn.close()
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130

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
<<<<<<< HEAD
    try:
        from_account = input("From Account ID: ").strip()
        to_account = input("To Account ID: ").strip()
        amount = float(input("Amount: $").strip())
=======
    conn = None
    cursor = None
    try:
        from_account = ask_int("From Account ID: ")
        to_account = ask_int("To Account ID: ")
        amount = float(ask_amount("Amount: $"))
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify from account exists and has enough balance
        cursor.execute("SELECT * FROM Account WHERE account_id = %s AND status = 'active'", (from_account,))
        source = cursor.fetchone()

        if not source:
            print("Source account not found or inactive.")
            return

<<<<<<< HEAD
        if source["balance"] < amount:
=======
        if float(source["balance"]) < amount:
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
            print("Insufficient funds.")
            return

        # Verify to account exists
        cursor.execute("SELECT * FROM Account WHERE account_id = %s AND status = 'active'", (to_account,))
        destination = cursor.fetchone()

        if not destination:
            print("Destination account not found or inactive.")
            return

<<<<<<< HEAD
        # Execute transfer as a transaction
        conn.start_transaction()

=======
        
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
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
<<<<<<< HEAD
        conn.rollback()
=======
        if conn:
            conn.rollback()
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130
        log_error(user.get("login_id", "unknown"), "TRANSFER", str(e))
        print(f"Transfer failed: {e}")

    finally:
<<<<<<< HEAD
        cursor.close()
        conn.close()
=======
        if cursor:
            cursor.close()
        if conn:
            conn.close()
>>>>>>> a88a621940c18984e3a571d44d649ff159bc5130

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
