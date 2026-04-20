import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

# ---------------- DATABASE ----------------
def get_connection():
    return sqlite3.connect("parking.db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS parking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    parking_lot INTEGER,
    owner_name TEXT,
    aadhar TEXT,
    phone TEXT,
    vehicle_type TEXT,
    car_number TEXT,
    slot_status TEXT,
    start_date TEXT,
    end_date TEXT,
    payment_date TEXT,
    payment_mode TEXT,
    receipt_number TEXT,
    advance_paid TEXT,
    amount_received REAL,
    late_fee REAL,
    total_amount REAL,
    balance REAL,
    remarks TEXT
)
""")
conn.commit()

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Sivagiri Parking Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ---------------- PDF RECEIPT ----------------
def generate_receipt(row):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Sivagiri Parking Receipt", styles["Title"]))
    content.append(Paragraph(f"Owner: {row['owner_name']}", styles["Normal"]))
    content.append(Paragraph(f"Car Number: {row['car_number']}", styles["Normal"]))
    content.append(Paragraph(f"Parking Slot: {row['parking_lot']}", styles["Normal"]))
    content.append(Paragraph(f"Month: {row['month']}", styles["Normal"]))
    content.append(Paragraph(f"Paid: ₹{row['amount_received']}", styles["Normal"]))
    content.append(Paragraph(f"Balance: ₹{row['balance']}", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)
    return buffer

# ---------------- MENU ----------------
st.sidebar.title("🚗 Sivagiri Parking")
menu = st.sidebar.selectbox("Menu", [
    "Add Entry",
    "View Records",
    "Unpaid Users",
    "Monthly Report"
])

# ---------------- ADD ENTRY ----------------
if menu == "Add Entry":
    st.header("Add Parking Entry")

    month = st.text_input("Month (e.g. Apr-2026)")
    parking_lot = st.selectbox("Parking Lot", list(range(101,131)))
    owner = st.text_input("Owner Name")
    aadhar = st.text_input("Aadhar Number")
    phone = st.text_input("Phone Number")
    vehicle = st.selectbox("Vehicle Type", ["Car","SUV","Other"])
    car_no = st.text_input("Car Number")
    status = st.selectbox("Slot Status", ["Occupied","Vacant"])

    start = st.date_input("Start Date", value=date.today())
    end = st.date_input("End Date", value=date.today())
    payment_date = st.date_input("Payment Date", value=date.today())

    payment_mode = st.selectbox("Payment Mode", ["Cash","UPI","Bank"])
    receipt = st.text_input("Receipt Number")
    advance = st.selectbox("Advance Paid", ["Yes","No"])

    amount = st.number_input("Amount Received", min_value=0.0)
    late_fee = st.number_input("Late Fee", min_value=0.0)

    total = 1100
    balance = total - amount - late_fee

    st.write(f"### Balance: ₹{balance}")

    remarks = st.text_area("Remarks")

    if st.button("Save Entry"):
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
            month, parking_lot, owner, aadhar, phone,
            vehicle, car_no, status,
            str(start), str(end), str(payment_date),
            payment_mode, receipt, advance,
            amount, late_fee, total, balance, remarks
        )

        cursor.execute(query, values)
        conn.commit()
        st.success("✅ Entry saved successfully!")

# ---------------- VIEW RECORDS ----------------
elif menu == "View Records":
    st.header("All Records")

    df = pd.read_sql_query("SELECT * FROM parking_records", conn)

    def highlight(row):
        if row["balance"] > 0:
            return ["background-color: red"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(highlight, axis=1))

    st.subheader("Download Receipts")

    for _, row in df.iterrows():
        pdf = generate_receipt(row)

        st.download_button(
            label=f"Download Receipt - {row['owner_name']}",
            data=pdf,
            file_name=f"{row['owner_name']}_receipt.pdf",
            mime="application/pdf"
        )

# ---------------- UNPAID USERS ----------------
elif menu == "Unpaid Users":
    st.header("Unpaid Users")

    df = pd.read_sql_query(
        "SELECT * FROM parking_records WHERE balance > 0", conn
    )

    st.dataframe(df)

# ---------------- MONTHLY REPORT ----------------
elif menu == "Monthly Report":
    st.header("Monthly Report")

    month_filter = st.text_input("Enter Month (e.g. Apr-2026)")

    if st.button("Generate Report"):
        query = f"""
        SELECT owner_name, parking_lot, amount_received, balance
        FROM parking_records
        WHERE month = '{month_filter}'
        """

        df = pd.read_sql_query(query, conn)

        st.dataframe(df)

        total_collected = df["amount_received"].sum()
        total_pending = df["balance"].sum()

        st.write(f"### Total Collected: ₹{total_collected}")
        st.write(f"### Total Pending: ₹{total_pending}")

        csv = df.to_csv(index=False)

        st.download_button(
            "Download CSV",
            csv,
            "monthly_report.csv",
            "text/csv"
        )
