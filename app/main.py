# SJSU CMPE 138 SPRING 2026 TEAM7

from __future__ import annotations

import bcrypt

from app.account_operations import AccountBankingService
from app.card_operations import CardBankingService
from app.db import get_connection
from app.loan_operations import LoanService
from app.evan_ops import EvanBankingService
from app.logger import log_action, log_error


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
        for key, value in result.payload.items():
            print(f"  {key}: {value}")
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


def login(conn):
    while True:
        print("\n=== Welcome to Team7 Banking System ===")
        print("Type 'exit' to quit.")
        username = input("Username: ").strip()

        if username.lower() in ("exit", "quit", "q"):
            return None

        password = input("Password: ").strip()
        cursor = conn.cursor(dictionary=True)

        # Check Employee first
        cursor.execute(
            """
            SELECT employee_id, login_id, role, status, password_hash, first_name, 'employee' AS user_type
            FROM Employee WHERE login_id = %s
            """,
            (username,),
        )
        user = cursor.fetchone()

        # Check Customer
        if user is None:
            cursor.execute(
                """
                SELECT customer_id, username AS login_id, 'customer' AS role, status, password_hash, first_name, 'customer' AS user_type
                FROM Customer WHERE username = %s
                """,
                (username,),
            )
            user = cursor.fetchone()

        cursor.close()

        if user is None:
            print("Invalid username or password.")
            log_error(username, "LOGIN", "User not found")
            continue

        if user["status"] != "active":
            print("Account not active.")
            continue

        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            print("Invalid username or password.")
            log_error(username, "LOGIN", "Wrong password")
            continue

        print(f"\nWelcome, {user['first_name']}! Role: {user['role']}")
        log_action(username, "LOGIN", "Success")
        return user
    

def register(conn):
    print("\n=== Register for Online Banking ===")
    try:
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        dob = input("Date of birth (YYYY-MM-DD): ").strip()
        address = input("Address: ").strip()
        phone = input("Phone: ").strip()
        email = input("Email: ").strip()
        username = input("Choose a username: ").strip()
        password = input("Choose a password: ").strip()

        if not all([first_name, last_name, dob, address, phone, email, username, password]):
            print("All fields are required.")
            return

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        cursor = conn.cursor(dictionary=True)

        # Check if username or email already exists
        cursor.execute("SELECT customer_id FROM Customer WHERE username = %s OR email = %s", (username, email))
        existing = cursor.fetchone()
        if existing:
            print("Username or email already taken.")
            cursor.close()
            return

        cursor.execute("""
            INSERT INTO Customer
                (first_name, last_name, date_of_birth, address, phone, email, username, password_hash, status)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """, (first_name, last_name, dob, address, phone, email, username, password_hash))

        conn.commit()
        customer_id = cursor.lastrowid
        cursor.close()

        log_action(username, "REGISTER", f"New customer registered customer_id={customer_id}")
        print(f"\nRegistration successful! Your customer ID is {customer_id}.")
        print("You can now log in with your username and password.")

    except Exception as e:
        conn.rollback()
        log_error("register", "REGISTER", str(e))
        print(f"Registration failed: {e}")

# ---------------- CUSTOMER ----------------
def customer_menu(conn, user):
    evan_service = EvanBankingService(conn)
    card_service = CardBankingService(conn)

    while True:
        print("\n--- Customer Menu ---")
        print("1. View Accounts")
        print("2. View Transactions")
        print("3. Update Profile")
        print("4. Apply for Loan")
        print("5. View Loan Status")
        print("6. Make Loan Payment")
        print("7. Request Card")
        print("8. Report Card Lost")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            result = evan_service.view_accounts(user["customer_id"])
            if result["ok"]:
                print_rows("Accounts", result["rows"])
            else:
                print("\nERROR\n" + result["message"])

        elif choice == "2":
            result = evan_service.view_transactions(user["customer_id"])
            if result["ok"]:
                print_rows("Transactions", result["rows"])
            else:
                print("\nERROR\n" + result["message"])

        elif choice == "3":
            print("\nLeave blank to keep current value.")
            address = input("New address: ").strip()
            phone = input("New phone: ").strip()
            email = input("New email: ").strip()
            result = evan_service.update_profile(
                user["customer_id"],
                address=address or None,
                phone=phone or None,
                email=email or None,
            )
            print("\nSUCCESS" if result["ok"] else "\nERROR")
            print(result["message"])

        elif choice == "4":
            loan_amount = ask_amount("Loan amount: ")
            interest_rate = ask_amount("Interest rate (%): ")
            loan_terms = ask_int("Loan term (months): ")
            result = evan_service.apply_for_loan(
                user["customer_id"], loan_amount, interest_rate, loan_terms
            )
            print("\nSUCCESS" if result["ok"] else "\nERROR")
            print(result["message"])
            if result["ok"]:
                print(f"  Loan ID: {result['loan_id']}")
                print(f"  Monthly Payment: ${result['monthly_payment']}")

        elif choice == "5":
            result = evan_service.view_loan_status(user["customer_id"])
            if result["ok"]:
                print_rows("Loans", result["rows"])
            else:
                print("\nERROR\n" + result["message"])

        elif choice == "6":
            loan_id = input("Loan ID: ").strip()
            amount = input("Payment amount: ").strip()
            result = evan_service.make_loan_payment(user["customer_id"], loan_id, amount)
            print("\nSUCCESS" if result["ok"] else "\nERROR")
            print(result["message"])
            if result["ok"]:
                print(f"  Paid: ${result['paid_amount']}")
                print(f"  Remaining: ${result['remaining_balance']}")
                print(f"  Status: {result['loan_status']}")

        elif choice == "7":
            account_id = ask_int("Account ID: ")
            card_type = input("Card type (debit/credit): ").strip()
            result = card_service.request_new_card(account_id, card_type)
            print_result(result)

        elif choice == "8":
            card_id = ask_int("Card ID (blank for number): ", allow_blank=True)
            card_number = None
            if card_id is None:
                card_number = input("Card number: ")
            result = card_service.report_card_lost(card_id, card_number)
            print_result(result)

        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")


# ---------------- TELLER ----------------
def teller_menu(conn, user):
    account_service = AccountBankingService(conn)

    while True:
        print("\n--- Teller Menu ---")
        print("1. Process Deposit")
        print("2. Process Withdrawal")
        print("3. Open Account")
        print("4. Close Account")
        print("5. Transfer Funds")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            account_id = ask_int("Account ID: ")
            amount = ask_amount("Amount: ")
            description = input("Description [deposit]: ").strip() or "deposit"
            result = account_service.process_deposit(account_id, amount, user["employee_id"], description)
            print_result(result)

        elif choice == "2":
            account_id = ask_int("Account ID: ")
            amount = ask_amount("Amount: ")
            description = input("Description [withdrawal]: ").strip() or "withdrawal"
            result = account_service.process_withdrawal(account_id, amount, user["employee_id"], description)
            print_result(result)

        elif choice == "3":
            customer_id = ask_int("Customer ID: ")
            account_type = input("Account type (checking/savings): ").strip()
            opening_deposit = ask_amount("Opening deposit (0 allowed): ", allow_zero=True)
            result = account_service.open_account(customer_id, account_type, opening_deposit, user["employee_id"])
            print_result(result)

        elif choice == "4":
            account_id = ask_int("Account ID: ")
            result = account_service.close_account(account_id)
            print_result(result)

        elif choice == "5":
            from_id = ask_int("From Account ID: ")
            to_id = ask_int("To Account ID: ")
            amount = ask_amount("Amount: ")
            result = account_service.transfer_funds(from_id, to_id, amount, user["employee_id"])
            print_result(result)

        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")


# ---------------- LOAN OFFICER ----------------
def loan_officer_menu(conn, user):
    loan_service = LoanService(conn)

    while True:
        print("\n--- Loan Officer Menu ---")
        print("1. Review Pending Loans")
        print("2. Approve Loan")
        print("3. Reject Loan")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            result = loan_service.review_loans()
            if result.ok and result.payload:
                print_rows("Pending Loans", result.payload["loans"])
            else:
                print_result(result)

        elif choice == "2":
            loan_id = ask_int("Loan ID: ")
            result = loan_service.approve_loan(loan_id, user["employee_id"])
            print_result(result)

        elif choice == "3":
            loan_id = ask_int("Loan ID: ")
            result = loan_service.reject_loan(loan_id, user["employee_id"])
            print_result(result)

        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")


# ---------------- MANAGER ----------------
def manager_menu(conn, user):
    account_service = AccountBankingService(conn)
    loan_service = LoanService(conn)

    while True:
        print("\n--- Manager Menu ---")
        print("1. Process Deposit")
        print("2. Process Withdrawal")
        print("3. Open Account")
        print("4. Close Account")
        print("5. Transfer Funds")
        print("6. Review Pending Loans")
        print("7. Approve Loan")
        print("8. Reject Loan")
        print("0. Logout")
        choice = input("Select: ").strip()

        if choice == "1":
            result = account_service.process_deposit(ask_int("Account ID: "), ask_amount("Amount: "), user["employee_id"])
            print_result(result)
        elif choice == "2":
            result = account_service.process_withdrawal(ask_int("Account ID: "), ask_amount("Amount: "), user["employee_id"])
            print_result(result)
        elif choice == "3":
            result = account_service.open_account(ask_int("Customer ID: "), input("Type (checking/savings): "), 0, user["employee_id"])
            print_result(result)
        elif choice == "4":
            result = account_service.close_account(ask_int("Account ID: "))
            print_result(result)
        elif choice == "5":
            result = account_service.transfer_funds(ask_int("From: "), ask_int("To: "), ask_amount("Amount: "), user["employee_id"])
            print_result(result)
        elif choice == "6":
            result = loan_service.review_loans()
            if result.ok and result.payload:
                print_rows("Pending Loans", result.payload["loans"])
            else:
                print_result(result)
        elif choice == "7":
            result = loan_service.approve_loan(ask_int("Loan ID: "), user["employee_id"])
            print_result(result)
        elif choice == "8":
            result = loan_service.reject_loan(ask_int("Loan ID: "), user["employee_id"])
            print_result(result)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")


# ---------------- MAIN ----------------
def main():
    conn = get_connection()

    while True:
        print("\n=== Team7 Banking System ===")
        print("1. Login")
        print("2. Register")
        print("0. Exit")
        choice = input("Select: ").strip()

        if choice == "1":
            user = login(conn)
            if user is None:
                continue

            role = user["role"]
            if role == "customer":
                customer_menu(conn, user)
            elif role == "teller":
                teller_menu(conn, user)
            elif role == "loan_officer":
                loan_officer_menu(conn, user)
            elif role == "manager":
                manager_menu(conn, user)

        elif choice == "2":
            register(conn)

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
