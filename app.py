import streamlit as st
import pandas as pd
from db import get_connection

st.title("🚗 Parking Management System")
# --- LOGIN ---
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid credentials")

# Session check
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

menu = st.sidebar.selectbox("Menu", ["Add Entry", "View Records", "Unpaid Users", "Monthly Report"])

# ---------------- ADD ENTRY ----------------
if menu == "Add Entry":
    st.subheader("Add Monthly Record")

    month = st.text_input("Month (e.g. Apr-2026)")
    parking_lot = st.selectbox("Parking Lot", list(range(101,131)))
    owner = st.text_input("Owner Name")
    aadhar = st.text_input("Aadhar Number")
    phone = st.text_input("Phone Number")
    vehicle = st.selectbox("Vehicle Type", ["Car","SUV","Other"])
    car_no = st.text_input("Car Number")
    status = st.selectbox("Slot Status", ["Occupied","Vacant"])

    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    payment_date = st.date_input("Payment Date")

    payment_mode = st.selectbox("Payment Mode", ["Cash","UPI","Bank"])
    receipt = st.text_input("Receipt Number")
    advance = st.selectbox("Advance Paid", ["Yes","No"])

    amount = st.number_input("Amount Received", min_value=0.0)
    late_fee = st.number_input("Late Fee", min_value=0.0)

    total = 1100
    balance = total - amount - late_fee

    st.write(f"### Balance: ₹{balance}")

    remarks = st.text_area("Remarks")

    if st.button("Save"):
        conn = get_connection()
        cursor = conn.cursor()

        #query = """
       # INSERT INTO parking_records (
    #    month, parking_lot, owner_name, aadhar, phone,
     #   vehicle_type, car_number, slot_status,
        #start_date, end_date, payment_date,
      #  payment_mode, receipt_number, advance_paid,
      #  amount_received, late_fee, total_amount, balance, remarks
      #  )
#VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
     #   """
        query = """
        INSERT INTO parking_records (
        month, parking_lot, owner_name, aadhar, phone,
        vehicle_type, car_number, slot_status,
        start_date, end_date, payment_date,
        payment_mode, receipt_number, advance_paid,
        amount_received, late_fee, total_amount, balance, remarks
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

        values = (
            month, parking_lot, owner_name, aadhar, phone,
            vehicle_type, car_number, slot_status,
            start_date, end_date, payment_date,
            payment_mode, receipt_number, advance_paid,
            amount_received, late_fee, total_amount, balance, remarks
        )

        cursor.execute(query, values)
        conn.commit()
        st.success("Saved successfully!")

# ---------------- VIEW RECORDS ----------------
elif menu == "View Records":
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM parking_records", conn)
    st.dataframe(df)

# ---------------- UNPAID USERS ----------------
elif menu == "Unpaid Users":
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM parking_records WHERE balance > 0", conn)
    st.dataframe(df)

# ---------------- MONTHLY REPORT ----------------
elif menu == "Monthly Report":
    month_filter = st.text_input("Enter Month (e.g. Apr-2026)")

    if st.button("Generate Report"):
        conn = get_connection()
        query = f"""
        SELECT owner_name, parking_lot, amount_received, balance
        FROM parking_records
        WHERE month = '{month_filter}'
        """
        df = pd.read_sql(query, conn)

        st.dataframe(df)

        total_collected = df["amount_received"].sum()
        total_pending = df["balance"].sum()

        st.write(f"### Total Collected: ₹{total_collected}")
        st.write(f"### Total Pending: ₹{total_pending}")

        # Export
        csv = df.to_csv(index=False)
        st.download_button("Download Report", csv, "report.csv")
