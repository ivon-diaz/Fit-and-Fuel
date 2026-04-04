### LOGIN SCREEN

import streamlit as st
from database import create_tables, create_user, verify_user


st.set_page_config(page_title="Fit and Fuel", page_icon="💪", layout="centered")

create_tables()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = None


def login_screen():
    st.title("Fit and Fuel")
    st.subheader("Login or Create an Account")
