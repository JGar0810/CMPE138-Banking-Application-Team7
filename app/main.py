# SJSU CMPE 138 SPRING 2026 TEAM7

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
            pass  # Ahmad fills this in
        elif choice == "2":
            pass  # Ahmad fills this in
        elif choice == "3":
            pass  # Ahmad fills this in
        elif choice == "4":
            pass  # Ahmad fills this in
        elif choice == "5":
            transfer_funds(user)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid option.")

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
