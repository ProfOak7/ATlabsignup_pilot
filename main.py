import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Student Appointment Sign-Up", layout="centered")

BOOKINGS_FILE = "bookings.csv"
ADMIN_PASSCODE = "cougar2025"  # You can change this!

# Load or create bookings file
if os.path.exists(BOOKINGS_FILE):
    bookings_df = pd.read_csv(BOOKINGS_FILE)
else:
    bookings_df = pd.DataFrame(columns=["email", "student_id", "dsps", "slot"])

# --- Generate next week's Mon–Fri with 15-min slots ---
today = datetime.today()
days = []
for i in range(7):
    d = today + timedelta(days=i)
    if d.weekday() < 5:  # Mon–Fri
        days.append(d)

single_slots = []
slot_mapping = {}  # Start–end time pairs for display

for day in days:
    current_time = datetime.combine(day.date(), datetime.strptime("09:00", "%H:%M").time())
    end_time = datetime.combine(day.date(), datetime.strptime("17:00", "%H:%M").time())
    while current_time < end_time:
        start_label = current_time.strftime("%-I:%M")
        end_label = (current_time + timedelta(minutes=15)).strftime("%-I:%M %p")
        slot_time_label = f"{start_label}–{end_label}"
        label = f"{day.strftime('%A %m/%d/%y')} {slot_time_label}"
        single_slots.append(label)
        slot_mapping[label] = (current_time, current_time + timedelta(minutes=15))
        current_time += timedelta(minutes=15)

# --- Generate DSPS double blocks (adjacent pairs) ---
double_blocks = {}
for i in range(len(single_slots) - 1):
    date1 = single_slots[i].split(" ")[1]
    date2 = single_slots[i+1].split(" ")[1]
    if date1 == date2:
        block_label = f"{single_slots[i]} and {single_slots[i+1]}"
        double_blocks[block_label] = [single_slots[i], single_slots[i+1]]

# --- UI: Login and Input ---
st.title("Student Appointment Sign-Up")

email = st.text_input("Enter your official Cuesta email:")
student_id = st.text_input("Enter your Student ID:")
dsps = st.checkbox("I am a DSPS student")

if email:
    if not email.lower().endswith("@my.cuesta.edu"):
        st.error("Please use your official Cuesta email ending in @my.cuesta.edu")
        st.stop()

if email and student_id:
    # Check if student already booked
    booked_this_week = bookings_df[bookings_df["email"] == email]
    if not booked_this_week.empty:
        st.warning("You’ve already booked your allowed slot(s) this week.")
        st.stop()

    st.subheader("Available Time Slots")

    if dsps:
        for label, pair in double_blocks.items():
            if not any(s in bookings_df["slot"].values for s in pair):
                if st.button(f"Book {label}"):
                    for s in pair:
                        new_booking = pd.DataFrame([{
                            "email": email,
                            "student_id": student_id,
                            "dsps": dsps,
                            "slot": s
                        }])
                        bookings_df = pd.concat([bookings_df, new_booking], ignore_index=True)
                    bookings_df.to_csv(BOOKINGS_FILE, index=False)
                    st.success(f"Successfully booked {label}!")
                    st.stop()
    else:
        for slot in single_slots:
            if slot not in bookings_df["slot"].values:
                if st.button(f"Book {slot}"):
                    new_booking = pd.DataFrame([{
                        "email": email,
                        "student_id": student_id,
                        "dsps": dsps,
                        "slot": slot
                    }])
                    bookings_df = pd.concat([bookings_df, new_booking], ignore_index=True)
                    bookings_df.to_csv(BOOKINGS_FILE, index=False)
                    st.success(f"Successfully booked {slot}!")
                    st.stop()

# --- Admin Access ---
st.markdown("---")
with st.expander("🔐 Admin Access"):
    passcode_input = st.text_input("Enter admin passcode:", type="password")

    if passcode_input == ADMIN_PASSCODE:
        st.success("Access granted.")
        st.dataframe(bookings_df)
        st.download_button("📤 Download CSV", bookings_df.to_csv(index=False), file_name="bookings.csv")
    elif passcode_input:
        st.error("Incorrect passcode.")
