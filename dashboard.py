import streamlit as st
import pandas as pd
import os
from datetime import date

LOANS_FILE = "loans.csv"
LEDGER_FILE = "ledger.csv"

st.title("Debt Repayment Dashboard")

# ------------------------------------------------
# Initialize files
# ------------------------------------------------
if not os.path.exists(LOANS_FILE):
    pd.DataFrame(columns=["loan_id","loan_category","date_created","amount"]).to_csv(LOANS_FILE,index=False)

if not os.path.exists(LEDGER_FILE):
    pd.DataFrame(columns=["date","loan_id","transaction_type","amount","balance_after"]).to_csv(LEDGER_FILE,index=False)

# ------------------------------------------------
# Load data
# ------------------------------------------------
loans_df = pd.read_csv(LOANS_FILE)
ledger_df = pd.read_csv(LEDGER_FILE)

if not loans_df.empty:
    loans_df["date_created"] = pd.to_datetime(loans_df["date_created"])

if not ledger_df.empty:
    ledger_df["date"] = pd.to_datetime(ledger_df["date"])

# ------------------------------------------------
# Helper functions
# ------------------------------------------------
def get_balances():
    balances = {}
    if not ledger_df.empty:
        for _, row in ledger_df.iterrows():
            balances[row["loan_id"]] = row["balance_after"]
    return balances

def add_ledger_entry(loan_id, ttype, amount, balance):
    new_row = pd.DataFrame([[date.today(), loan_id, ttype, amount, balance]],
                           columns=["date","loan_id","transaction_type","amount","balance_after"])
    new_row.to_csv(LEDGER_FILE, mode="a", header=False, index=False)

def add_loan(loan_id, category, amount):
    new_loan = pd.DataFrame([[loan_id, category, date.today(), amount]],
                            columns=["loan_id","loan_category","date_created","amount"])
    new_loan.to_csv(LOANS_FILE, mode="a", header=False, index=False)
    add_ledger_entry(loan_id, "loan_added", amount, amount)

def apply_payment(payment_amount):
    balances = get_balances()
    remaining = payment_amount

    additional = loans_df[loans_df["loan_category"]=="Additional"].sort_values("date_created", ascending=False)
    initial = loans_df[loans_df["loan_category"]=="Initial"]

    # pay additional first
    for _, loan in additional.iterrows():
        if remaining <= 0:
            break
        loan_id = loan["loan_id"]
        balance = balances.get(loan_id, loan["amount"])
        if balance <= 0:
            continue
        pay = min(balance, remaining)
        new_balance = balance - pay
        add_ledger_entry(loan_id, "payment", -pay, new_balance)
        remaining -= pay

    # then initial
    for _, loan in initial.iterrows():
        if remaining <= 0:
            break
        loan_id = loan["loan_id"]
        balance = balances.get(loan_id, loan["amount"])
        pay = min(balance, remaining)
        new_balance = balance - pay
        add_ledger_entry(loan_id, "payment", -pay, new_balance)
        remaining -= pay

# ------------------------------------------------
# Add Loan
# ------------------------------------------------
st.subheader("Add Loan")

with st.form("loan_form"):
    loan_id = st.text_input("Loan ID")
    category = st.selectbox("Category", ["Initial","Additional"])
    amount = st.number_input("Amount", step=1000)
    submit = st.form_submit_button("Add Loan")

    if submit and loan_id and amount > 0:
        add_loan(loan_id, category, amount)
        st.success("Loan Added")
        st.rerun()

# ------------------------------------------------
# Add Payment
# ------------------------------------------------
st.subheader("Make Payment")

payment = st.number_input("Payment Amount", step=1000)

if st.button("Apply Payment") and payment > 0:
    apply_payment(payment)
    st.success("Payment Applied")
    st.rerun()

# ------------------------------------------------
# Reload after updates
# ------------------------------------------------
loans_df = pd.read_csv(LOANS_FILE)
ledger_df = pd.read_csv(LEDGER_FILE)

if not loans_df.empty:
    loans_df["date_created"] = pd.to_datetime(loans_df["date_created"])

if not ledger_df.empty:
    ledger_df["date"] = pd.to_datetime(ledger_df["date"])

# ------------------------------------------------
# Build debt status
# ------------------------------------------------
balances = get_balances()

results = []

for _, loan in loans_df.iterrows():

    loan_id = loan["loan_id"]
    original = loan["amount"]
    remaining = balances.get(loan_id, original)
    paid = original - remaining

    status = "Repaid" if remaining <= 0 else "Unpaid"

    results.append({
        "loan_id": loan_id,
        "category": loan["loan_category"],
        "date": loan["date_created"],
        "original": original,
        "paid": paid,
        "remaining": remaining,
        "status": status
    })

result_df = pd.DataFrame(results).sort_values("date")

# ------------------------------------------------
# Overview
# ------------------------------------------------
st.subheader("Overview")

total_debt = result_df["original"].sum()
remaining_debt = result_df["remaining"].sum()
total_paid = total_debt - remaining_debt

col1,col2,col3 = st.columns(3)

col1.metric("Total Debt", f"¥{total_debt:,}")
col2.metric("Total Paid", f"¥{total_paid:,}")
col3.metric("Remaining Debt", f"¥{remaining_debt:,}")

st.divider()

# ------------------------------------------------
# Debt Table
# ------------------------------------------------
st.subheader("Debt Status")
st.dataframe(result_df)

# ------------------------------------------------
# Charts
# ------------------------------------------------
st.subheader("Debt Breakdown")
chart_df = result_df.set_index("date")[["original","remaining"]]
st.bar_chart(chart_df)

st.subheader("Repayment Progress")
progress_df = result_df.set_index("date")[["paid","remaining"]]
st.bar_chart(progress_df)

# ------------------------------------------------
# Balance timeline
# ------------------------------------------------
if not ledger_df.empty:
    ledger_df = ledger_df.sort_values("date")
    ledger_df["total_balance"] = ledger_df["amount"].cumsum()

    st.subheader("Balance Over Time")
    st.line_chart(ledger_df.set_index("date")["total_balance"])

# ------------------------------------------------
# Ledger view
# ------------------------------------------------
st.subheader("Ledger History")
st.dataframe(ledger_df)