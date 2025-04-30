import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="Student Appointment Sign-Up", layout="wide")

BOOKINGS_FILE = "bookings.csv"
AVAILABLE_FILE = "available_slots.csv"
ADMIN_PASSCODE = st.secrets["ADMIN_PASSCODE"]
AVAILABILITY_PASSCODE = st.secrets["AVAILABILITY_PASSCODE"]

# --- Initialize Session State ---
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
if "confirming" not in st.session_state:
    st.session_state.confirming = False

# --- Load or Initialize Bookings ---
if os.path.exists(BOOKINGS_FILE):
    bookings_df = pd.read_csv(BOOKINGS_FILE)
else:
    bookings_df = pd.DataFrame(columns=["name", "email", "student_id", "dsps", "slot"])

if "lab_location" not in bookings_df.columns:
    bookings_df["lab_location"] = "SLO AT Lab"

# --- Generate Slot Templates ---
today = datetime.today()
days = [today + timedelta(days=i) for i in range(21)]

slo_hours = {
    0: ("09:00", "21:00"),
    1: ("09:00", "21:00"),
    2: ("08:30", "21:00"),
    3: ("08:15", "20:30"),
    4: ("09:15", "15:00"),
    5: ("09:15", "13:00")
}

ncc_hours = {
    0: ("12:00", "16:00"),
    1: ("08:15", "20:00"),
    2: ("08:15", "17:00"),
    3: ("09:15", "17:00"),
    4: ("08:15", "15:00")
}

slo_single_slots, ncc_single_slots = [], []
slo_slots_by_day, ncc_slots_by_day = {}, {}

for day in days:
    weekday = day.weekday()
    label_day = day.strftime('%A %m/%d/%y')

    if weekday in slo_hours:
        start_str, end_str = slo_hours[weekday]
        current_time = datetime.combine(day.date(), datetime.strptime(start_str, "%H:%M").time())
        end_time = datetime.combine(day.date(), datetime.strptime(end_str, "%H:%M").time())
        while current_time < end_time:
            slot = f"{label_day} {current_time.strftime('%-I:%M')}\u2013{(current_time + timedelta(minutes=15)).strftime('%-I:%M %p')}"
            slo_slots_by_day.setdefault(label_day, []).append(slot)
            slo_single_slots.append(slot)
            current_time += timedelta(minutes=15)

    if weekday in ncc_hours:
        start_str, end_str = ncc_hours[weekday]
        current_time = datetime.combine(day.date(), datetime.strptime(start_str, "%H:%M").time())
        end_time = datetime.combine(day.date(), datetime.strptime(end_str, "%H:%M").time())
        while current_time < end_time:
            slot = f"{label_day} {current_time.strftime('%-I:%M')}\u2013{(current_time + timedelta(minutes=15)).strftime('%-I:%M %p')}"
            ncc_slots_by_day.setdefault(label_day, []).append(slot)
            ncc_single_slots.append(slot)
            current_time += timedelta(minutes=15)

all_single_slots = slo_single_slots + ncc_single_slots

# --- Navigation ---
st.sidebar.title("Navigation")
selected_tab = st.sidebar.radio("Go to:", ["Sign-Up", "Admin View", "Availability Settings"])

# --- Student Sign-Up Tab ---
if selected_tab == "Sign-Up":
    st.title("Student AT Appointment Sign-Up")

    lab_location = st.selectbox("Choose your AT Lab location:", ["SLO AT Lab", "NCC AT Lab"])
    slots_by_day = slo_slots_by_day if lab_location == "SLO AT Lab" else ncc_slots_by_day

    st.subheader("Current Sign-Ups")
    if not bookings_df.empty:
        calendar_data = bookings_df[bookings_df["lab_location"] == lab_location]
        if not calendar_data.empty:
            calendar_data["first_name"] = calendar_data["name"].apply(lambda x: x.split()[0])
            calendar_data["day"] = calendar_data["slot"].apply(lambda x: " ".join(x.split()[:2]))
            grouped = calendar_data.groupby("day")
            sorted_days = sorted(grouped.groups.keys(), key=lambda d: datetime.strptime(d.split()[1], "%m/%d/%y"))
            for day in sorted_days:
                with st.expander(f"{day} ({len(grouped.get_group(day))} sign-up{'s' if len(grouped.get_group(day)) != 1 else ''})"):
                    details = grouped.get_group(day)[["first_name", "slot"]].values.tolist()
                    for first_name, slot in details:
                        st.write(f"{first_name} - {slot}")
        else:
            st.info("No appointments scheduled for this lab yet.")
    else:
        st.info("No appointments scheduled yet.")

    # Sign-Up Form
    name = st.text_input("Enter your full name:")
    email = st.text_input("Enter your official Cuesta email:")
    student_id = st.text_input("Enter your Student ID:")
    dsps = st.checkbox("I am a DSPS student")

    if email and not (email.lower().endswith("@my.cuesta.edu") or email.lower().endswith("@cuesta.edu")):
        st.error("Please use your official Cuesta email ending in @my.cuesta.edu or @cuesta.edu")
        st.stop()

    if name and email and student_id:
        if not student_id.startswith("900"):
            st.error("Student ID must start with 900.")
            st.stop()

        st.subheader("Available Time Slots")
        selected_day = st.selectbox("Choose a day:", list(slots_by_day.keys()))
        available_slots = [
            s for s in slots_by_day[selected_day]
            if s not in bookings_df["slot"].values and
            datetime.strptime(f"{s.split()[1]} {s.split()[2].split('–')[0]} {s.split()[3]}", "%m/%d/%y %I:%M %p") > datetime.now()
        ]

        double_blocks = {}
        for i in range(len(slots_by_day[selected_day]) - 1):
            if slots_by_day[selected_day][i].split()[1] == slots_by_day[selected_day][i + 1].split()[1]:
                double_blocks[f"{slots_by_day[selected_day][i]} and {slots_by_day[selected_day][i + 1]}"] = [
                    slots_by_day[selected_day][i], slots_by_day[selected_day][i + 1]
                ]

        if dsps:
            double_slot_options = [
                label for label in double_blocks
                if all(
                    s not in bookings_df["slot"].values and
                    datetime.strptime(f"{s.split()[1]} {s.split()[2].split('–')[0]} {s.split()[3]}", "%m/%d/%y %I:%M %p") > datetime.now()
                    for s in double_blocks[label]
                )
            ]
            if double_slot_options:
                selected_block = st.selectbox("Choose a double time block:", double_slot_options)
                if st.button("Select This Time Block"):
                    st.session_state.selected_slot = selected_block
                    st.session_state.confirming = True
                    st.rerun()
            else:
                st.info("No available double blocks for this day.")
        else:
            if available_slots:
                selected_time = st.selectbox("Choose a time:", available_slots)
                if st.button("Select This Time"):
                    st.session_state.selected_slot = selected_time
                    st.session_state.confirming = True
                    st.rerun()
            else:
                st.info("No available slots for this day.")

    if st.session_state.confirming and st.session_state.selected_slot:
        st.subheader("Confirm Your Appointment")
        st.write(f"You have selected: **{st.session_state.selected_slot}**")

        if st.button("Confirm"):
            selected_week = datetime.strptime(st.session_state.selected_slot.split(" ")[1], "%m/%d/%y").isocalendar().week
            booked_weeks = bookings_df[bookings_df["email"] == email]["slot"].apply(
                lambda s: datetime.strptime(s.split(" ")[1], "%m/%d/%y").isocalendar().week
            )

            if selected_week in booked_weeks.values:
                st.warning("You already have a booking this week. Your previous booking will be replaced.")
                bookings_df = bookings_df[~((bookings_df["email"] == email) & (bookings_df["slot"].apply(
                    lambda s: datetime.strptime(s.split(" ")[1], "%m/%d/%y").isocalendar().week == selected_week)))]

            if dsps and " and " in st.session_state.selected_slot:
                for s in st.session_state.selected_slot.split(" and "):
                    new_booking = pd.DataFrame([{ "name": name, "email": email, "student_id": student_id, "dsps": dsps, "slot": s, "lab_location": lab_location }])
                    bookings_df = pd.concat([bookings_df, new_booking], ignore_index=True)
            else:
                new_booking = pd.DataFrame([{ "name": name, "email": email, "student_id": student_id, "dsps": dsps, "slot": st.session_state.selected_slot, "lab_location": lab_location }])
                bookings_df = pd.concat([bookings_df, new_booking], ignore_index=True)

            bookings_df.to_csv(BOOKINGS_FILE, index=False)
            st.success(f"Successfully booked {st.session_state.selected_slot}!")
            st.session_state.selected_slot = None
            st.session_state.confirming = False
            st.stop()

        if st.button("Cancel"):
            st.session_state.selected_slot = None
            st.session_state.confirming = False
            st.rerun()

# --- Admin View Tab ---
elif selected_tab == "Admin View":
    st.title("Admin Panel")
    passcode_input = st.text_input("Enter admin passcode:", type="password")

    if passcode_input == ADMIN_PASSCODE:
        st.success("Access granted.")

        # Separate bookings by lab location
        slo_bookings = bookings_df[bookings_df["lab_location"] == "SLO AT Lab"]
        ncc_bookings = bookings_df[bookings_df["lab_location"] == "NCC AT Lab"]

        st.subheader("SLO AT Lab Bookings")
        st.dataframe(slo_bookings)
        st.download_button("Download All SLO Bookings", slo_bookings.to_csv(index=False), file_name="slo_bookings.csv")

        st.subheader("NCC AT Lab Bookings")
        st.dataframe(ncc_bookings)
        st.download_button("Download All NCC Bookings", ncc_bookings.to_csv(index=False), file_name="ncc_bookings.csv")

        st.subheader("Download Today's Appointments")
        today_str = datetime.today().strftime("%m/%d/%y")

        todays_slo = slo_bookings[slo_bookings["slot"].str.contains(today_str)].copy()
        if not todays_slo.empty:
            todays_slo["slot_dt"] = todays_slo["slot"].apply(lambda x: datetime.strptime(f"{x.split()[1]} {x.split()[2].split('–')[0]} {x.split()[3]}", "%m/%d/%y %I:%M %p"))
            todays_slo = todays_slo.sort_values("slot_dt").drop(columns="slot_dt")
            st.download_button("Download Today's SLO Appointments", todays_slo.to_csv(index=False), file_name="todays_slo_appointments.csv")
        else:
            st.info("No SLO appointments scheduled for today.")

        todays_ncc = ncc_bookings[ncc_bookings["slot"].str.contains(today_str)].copy()
        if not todays_ncc.empty:
            todays_ncc["slot_dt"] = todays_ncc["slot"].apply(lambda x: datetime.strptime(f"{x.split()[1]} {x.split()[2].split('–')[0]} {x.split()[3]}", "%m/%d/%y %I:%M %p"))
            todays_ncc = todays_ncc.sort_values("slot_dt").drop(columns="slot_dt")
            st.download_button("Download Today's NCC Appointments", todays_ncc.to_csv(index=False), file_name="todays_ncc_appointments.csv")
        else:
            st.info("No NCC appointments scheduled for today.")

        st.subheader("Reschedule a Student Appointment")
        if not bookings_df.empty:
            options = [f"{row['name']} ({row['email']}) - {row['slot']}" for _, row in bookings_df.iterrows()]
            selected = st.selectbox("Select a booking to reschedule", options)
            index = options.index(selected)
            current_booking = bookings_df.iloc[index]

            # Group available slots by day like student view
            slots_by_day = slo_slots_by_day if current_booking["lab_location"] == "SLO AT Lab" else ncc_slots_by_day
            available_by_day = {
                day: [s for s in slots if s not in bookings_df["slot"].values or s == current_booking["slot"]]
                for day, slots in slots_by_day.items()
            }
            days_with_availability = [day for day in available_by_day if available_by_day[day]]

            selected_day = st.selectbox("Choose a new day:", days_with_availability)
            selected_slot = st.selectbox("Choose a new time:", available_by_day[selected_day])

            if st.button("Reschedule"):
                if current_booking["dsps"] and bookings_df[bookings_df["email"] == current_booking["email"]].shape[0] == 2:
                    # Move both DSPS blocks if applicable
                    old_slots = bookings_df[(bookings_df["email"] == current_booking["email"])]["slot"].tolist()
                    bookings_df = bookings_df[~(bookings_df["email"] == current_booking["email"])]
                    new_start = datetime.strptime(selected_slot.split()[1], "%m/%d/%y")
                    first_block = selected_slot
                    try:
                        second_block = slots_by_day[selected_day][slots_by_day[selected_day].index(first_block) + 1]
                        new_blocks = [first_block, second_block]
                        for s in new_blocks:
                            new_row = current_booking.copy()
                            new_row["slot"] = s
                            bookings_df = pd.concat([bookings_df, pd.DataFrame([new_row])], ignore_index=True)
                        bookings_df.to_csv(BOOKINGS_FILE, index=False)
                        st.success(f"Successfully rescheduled DSPS appointment to {first_block} and {second_block}!")
                    except IndexError:
                        st.error("Could not find a consecutive block for DSPS reschedule.")
                else:
                    bookings_df.at[index, "slot"] = selected_slot
                    bookings_df.to_csv(BOOKINGS_FILE, index=False)
                    st.success(f"Successfully rescheduled to {selected_slot}!")

    elif passcode_input:
        st.error("Incorrect passcode.")

# --- Availability Settings Tab (from old setup without SLO and NCC location differences) ---
elif selected_tab == "Availability Settings":
    st.title("Availability Settings")
    availability_passcode = st.text_input("Enter availability admin passcode:", type="password")

    if availability_passcode == AVAILABILITY_PASSCODE:
        st.success("Access granted to Availability Settings.")

        if os.path.exists(AVAILABLE_FILE):
            availability_df = pd.read_csv(AVAILABLE_FILE)
        else:
            availability_df = pd.DataFrame({"slot": single_slots, "available": [True]*len(single_slots)})

        selected_by_day = {}
        for day, slots in slots_by_day.items():
            with st.expander(day):
                if st.button(f"Select All {day}", key=f"select_all_{day}"):
                    for slot in slots:
                        st.session_state[f"avail_{slot}"] = True
                if st.button(f"Deselect All {day}", key=f"deselect_all_{day}"):
                    for slot in slots:
                        st.session_state[f"avail_{slot}"] = False

                selected_by_day[day] = []
                for slot in slots:
                    is_selected = availability_df.loc[availability_df["slot"] == slot, "available"].values[0] if slot in availability_df["slot"].values else False
                    checked = st.checkbox(slot.split()[-2] + " " + slot.split()[-1], value=st.session_state.get(f"avail_{slot}", is_selected), key=f"avail_{slot}")
                    if checked:
                        selected_by_day[day].append(slot)

        selected_available = [slot for slots in selected_by_day.values() for slot in slots]
        availability_df["available"] = availability_df["slot"].isin(selected_available)

        if st.button("Save Availability"):
            availability_df.to_csv(AVAILABLE_FILE, index=False)
            st.success("Availability updated successfully!")
    elif availability_passcode:
        st.error("Incorrect passcode.")
