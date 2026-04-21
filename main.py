from __future__ import annotations

from app.ahmad_ops import AhmadBankingService
from app.db import get_connection


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
            print(f"- {k}: {v}")
    print()


def main():
    conn = get_connection()
    service = AhmadBankingService(conn)
    try:
        while True:
            print("=" * 48)
            print("Ahmad CLI - Account Operations")
            print("1) Open account")
            print("2) Process deposit")
            print("3) Process withdrawal")
            print("4) Close account")
            print("5) Exit")
            choice = input("Choose an option: ").strip()

            if choice == "1":
                customer_id = ask_int("Customer ID: ")
                account_type = input("Account type (checking/savings): ").strip().lower()
                opening_deposit = ask_amount("Opening deposit (0 allowed): ", allow_zero=True)
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                result = service.open_account(customer_id, account_type, opening_deposit, teller_id)
                print_result(result)
            elif choice == "2":
                account_id = ask_int("Account ID: ")
                amount = ask_amount("Deposit amount: ")
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                description = input("Description [CLI deposit]: ").strip() or "CLI deposit"
                result = service.process_deposit(account_id, amount, teller_id, description)
                print_result(result)
            elif choice == "3":
                account_id = ask_int("Account ID: ")
                amount = ask_amount("Withdrawal amount: ")
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                description = input("Description [CLI withdrawal]: ").strip() or "CLI withdrawal"
                result = service.process_withdrawal(account_id, amount, teller_id, description)
                print_result(result)
            elif choice == "4":
                account_id = ask_int("Account ID: ")
                result = service.close_account(account_id)
                print_result(result)
            elif choice == "5":
                break
            else:
                print("Invalid choice.\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
