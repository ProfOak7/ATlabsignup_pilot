import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

ADMIN_PASSCODE = "OAK"  # You can change this to anything private

st.set_page_config(page_title="Student Appointment Sign-Up", layout="centered")

BOOKINGS_FILE = "bookings.csv"

# Load or create bookings file
if os.path.exists(BOOKINGS_FILE):
    bookings_df = pd.read_csv(BOOKINGS_FILE)
else:
    bookings_df = pd.DataFrame(columns=["email", "student_id", "dsps", "slot"])

# --- Generate 15-minute slots ---
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
start_time = datetime.strptime("09:00", "%H:%M")
end_time = datetime.strptime("17:00", "%H:%M")

single_slots = []
for day in days:
    current_time = start_time
    while current_time < end_time:
        label = f"{day} {current_time.strftime('%-I:%M %p')}"
        single_slots.append(label)
        current_time += timedelta(minutes=15)

# --- Generate DSPS double-slot blocks ---
double_blocks = {}
for i in range(len(single_slots) - 1):
    day1, time1 = single_slots[i].split(" ", 1)
    day2, time2 = single_slots[i+1].split(" ", 1)
    if day1 == day2:
        block_label = f"{day1} {time1}–{single_slots[i+1].split(' ', 1)[1]}"
        double_blocks[block_label] = [single_slots[i], single_slots[i+1]]

# --- UI: Title & Login ---
st.title("Student Appointment Sign-Up")

email = st.text_input("Enter your cuesta email:")
student_id = st.text_input("Enter your Student ID:")
dsps = st.checkbox("I am a DSPS student")

if email and student_id:
    # Check if student has already booked
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

# --- Optional Admin View ---
with st.expander("🔐 Admin Access"):
    passcode_input = st.text_input("Enter admin passcode:", type="password")

    if passcode_input == ADMIN_PASSCODE:
        st.success("Access granted.")
        st.dataframe(bookings_df)
        st.download_button("📤 Download CSV", bookings_df.to_csv(index=False), file_name="bookings.csv")
    elif passcode_input:
        st.error("Incorrect passcode.")
