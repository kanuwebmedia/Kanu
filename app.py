# --- Swachh Bharat App without MySQL (with local storage + better UI) ---

import streamlit as st
import hashlib
import json
import os
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime

# ------------ Helper Functions ------------

DATA_FILE = 'data.json'

# Create data file if doesn't exist
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"users": [], "entries": []}, f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------ Auth Functions ------------

def register_user(username, password, full_name):
    data = load_data()
    if any(u['username'] == username for u in data['users']):
        return False
    new_user = {
        "id": len(data['users']) + 1,
        "username": username,
        "password": hash_password(password),
        "full_name": full_name
    }
    data['users'].append(new_user)
    save_data(data)
    return True

def login_user(username, password):
    data = load_data()
    hashed = hash_password(password)
    for user in data['users']:
        if user['username'] == username and user['password'] == hashed:
            return user
    return None

# ------------ CRUD Functions ------------

def create_entry(user_id, household_name, father_name, mobile_no, address, dustbin_number, image_bytes):
    data = load_data()
    new_entry = {
        "id": len(data['entries']) + 1,
        "user_id": user_id,
        "household_name": household_name,
        "father_name": father_name,
        "mobile_no": mobile_no,
        "address": address,
        "dustbin_number": dustbin_number,
        "image": base64.b64encode(image_bytes).decode() if image_bytes else None,
        "created_at": datetime.now().isoformat()
    }
    data['entries'].append(new_entry)
    save_data(data)

def get_entries(user_id):
    data = load_data()
    return [e for e in data['entries'] if e['user_id'] == user_id]

def get_entry(entry_id):
    data = load_data()
    for e in data['entries']:
        if e['id'] == entry_id:
            return e
    return None

def update_entry(entry_id, household_name, father_name, mobile_no, address, dustbin_number):
    data = load_data()
    for e in data['entries']:
        if e['id'] == entry_id:
            e['household_name'] = household_name
            e['father_name'] = father_name
            e['mobile_no'] = mobile_no
            e['address'] = address
            e['dustbin_number'] = dustbin_number
    save_data(data)

def delete_entry(entry_id):
    data = load_data()
    data['entries'] = [e for e in data['entries'] if e['id'] != entry_id]
    save_data(data)

# ------------ PDF Export ------------

def export_to_pdf(entries):
    pdf = FPDF()
    pdf.set_font("Arial", size=10)
    pdf.add_page()

    pdf.cell(200, 10, txt="Entries Report", ln=True, align="C")
    pdf.ln(10)

    for idx, entry in enumerate(entries, 1):
        pdf.cell(0, 10, f"{idx}. {entry['household_name']} ({entry['father_name']}), Mobile: {entry['mobile_no']}", ln=True)
        pdf.cell(0, 10, f"Address: {entry['address']}, Dustbin No: {entry['dustbin_number']}", ln=True)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin1')

# ------------ Streamlit UI ------------

def main():
    st.set_page_config(page_title="Swachh Bharat App", page_icon="🌿", layout="wide")

    init_data()

    st.markdown("""
        <style>
            .main {background-color: #f8f9fa; padding:20px; border-radius:10px;}
            .title {text-align: center; color: green;}
            .stButton>button {background-color: #4CAF50; color: white;}
        </style>
    """, unsafe_allow_html=True)

    if 'user' not in st.session_state:
        st.session_state.user = None

    menu = ["Home", "Register", "Login", "Logout"] if not st.session_state.user else ["Home", "New Entry", "My Entries", "Logout"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Register":
        page_register()
    elif choice == "Login":
        page_login()
    elif choice == "Home":
        page_home()
    elif choice == "New Entry":
        page_new_entry()
    elif choice == "My Entries":
        page_entries()
    elif choice == "Logout":
        st.session_state.user = None
        st.success("Logged out successfully!")

# ------------ Pages ------------

def page_register():
    st.title("📅 Register")
    username = st.text_input("Username")
    full_name = st.text_input("Full Name")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if register_user(username, password, full_name):
            st.success("Registration successful. Please login.")
        else:
            st.error("Username already exists.")

def page_login():
    st.title("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user = user
            st.success(f"Welcome {user['full_name']}!")
        else:
            st.error("Invalid username or password.")

def page_home():
    st.title("🏠 Home")
    if st.session_state.user:
        st.success(f"Logged in as {st.session_state.user['full_name']}")
    else:
        st.info("Please login or register.")

def page_new_entry():
    st.title("📌 New Entry")
    household_name = st.text_input("Household Name")
    father_name = st.text_input("Father's Name")
    mobile_no = st.text_input("Mobile No.")
    address = st.text_area("Address")
    dustbin_number = st.number_input("Number of Dustbins", min_value=0, step=1)
    picture = st.camera_input("Take a Picture")

    if st.button("Save Entry"):
        img_bytes = picture.getvalue() if picture else None
        create_entry(st.session_state.user['id'], household_name, father_name, mobile_no, address, dustbin_number, img_bytes)
        st.success("Entry saved successfully!")

def page_entries():
    st.title("📊 My Entries")
    entries = get_entries(st.session_state.user['id'])

    if entries:
        df = pd.DataFrame([{**e, "Image": "📷" if e['image'] else "No"} for e in entries])
        st.dataframe(df[['household_name', 'father_name', 'mobile_no', 'address', 'dustbin_number', 'created_at', 'Image']])

        if st.button("Download PDF Report"):
            pdf_data = export_to_pdf(entries)
            st.download_button("Download", data=pdf_data, file_name="entries.pdf", mime="application/pdf")
    else:
        st.info("No entries found.")

# ------------ Run ------------

if __name__ == "__main__":
    main()
