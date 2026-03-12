import streamlit as st
import csv
from datetime import date, datetime

LOANS_FILE = "loans.csv"
LEDGER_FILE = "ledger.csv"

# ------------------ Functions (same as before) ------------------

def add_loan(loan_id, loan_category, amount):
    with open(LOANS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([loan_id, loan_category, date.today(), amount])
    add_ledger_entry(loan_id, "loan_added", amount, amount)

def load_loans():
    loans = []
    with open(LOANS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            loans.append({
                "loan_id": row["loan_id"],
                "loan_category": row["loan_category"],
                "date_created": datetime.strptime(row["date_created"], "%Y-%m-%d"),
                "amount": float(row["amount"])
            })
    return loans

def add_ledger_entry(loan_id, transaction_type, amount, balance_after):
    with open(LEDGER_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date.today(), loan_id, transaction_type, amount, balance_after])

def load_ledger_balances():
    balances = {}
    try:
        with open(LEDGER_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                balances[row["loan_id"]] = float(row["balance_after"])
    except FileNotFoundError:
        pass
    return balances

def add_payment(loan_id, payment_amount, notes=""):
    balances = load_ledger_balances()
    prev_balance = balances.get(loan_id, 0)
    new_balance = prev_balance - payment_amount
    add_ledger_entry(loan_id, f"payment:{notes}", -payment_amount, new_balance)

def apply_payment(payment_amount, notes=""):
    loans = load_loans()
    balances = load_ledger_balances()
    remaining = payment_amount

    additional_loans = [l for l in loans if l["loan_category"] == "Additional"]
    additional_loans.sort(key=lambda x: x["date_created"], reverse=True)

    for loan in additional_loans:
        loan_id = loan["loan_id"]
        balance = balances.get(loan_id, loan["amount"])
        if balance <= 0:
            continue
        pay = min(balance, remaining)
        add_payment(loan_id, pay, notes)
        remaining -= pay
        if remaining <= 0:
            return

    for loan in loans:
        if loan["loan_category"] == "Initial":
            add_payment(loan["loan_id"], remaining, notes)
            return

def calculate_balances():
    return load_ledger_balances()

def load_ledger():
    """Return full ledger as a list of dicts"""
    entries = []
    try:
        with open(LEDGER_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
    except FileNotFoundError:
        pass
    return entries

# ------------------ Streamlit Dashboard ------------------

st.title("📊 Loan & Payment Tracker Dashboard")

# Tabs for sections
tab1, tab2, tab3 = st.tabs(["Add Loan", "Make Payment", "View Ledger"])

with tab1:
    st.header("Add New Loan")
    loan_id = st.text_input("Loan ID")
    loan_category = st.selectbox("Category", ["Initial", "Additional"])
    amount = st.number_input("Amount", min_value=0.0, step=100.0)
    if st.button("Add Loan"):
        if loan_id and amount > 0:
            add_loan(loan_id, loan_category, amount)
            st.success(f"Loan {loan_id} added successfully.")
        else:
            st.error("Enter valid Loan ID and amount.")

with tab2:
    st.header("Make Payment")
    payment_amount = st.number_input("Payment Amount", min_value=0.0, step=100.0)
    notes = st.text_input("Notes (optional)")
    if st.button("Apply Payment"):
        if payment_amount > 0:
            apply_payment(payment_amount, notes)
            st.success(f"Payment of {payment_amount} applied automatically.")
        else:
            st.error("Enter a valid payment amount.")

with tab3:
    st.header("Current Balances")
    balances = calculate_balances()
    if balances:
        st.table(balances)
    else:
        st.info("No loans or payments yet.")

    st.subheader("Ledger History")
    ledger_entries = load_ledger()
    if ledger_entries:
        st.dataframe(ledger_entries)
    else:
        st.info("Ledger is empty.")