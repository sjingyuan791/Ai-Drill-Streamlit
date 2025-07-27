import streamlit as st
from auth import login_page, signup_page
from pages.drill_page import drill_main

# セッション管理
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.user_id is None:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    st.stop()
else:
    drill_main()
