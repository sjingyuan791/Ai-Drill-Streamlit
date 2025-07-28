import streamlit as st
from auth import login_page, signup_page
from pages.drill_page import drill_main
from profile_page import profile_page  # ← プロフィール編集ページを追加

# セッション管理
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = None  # ユーザー名（ニックネーム）初期化

if st.session_state.user_id is None:
    # ログイン前
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    st.stop()
else:
    # ログイン後、プロフィール（username）未登録の場合は編集画面に誘導
    if not st.session_state.get("username"):
        st.warning("ニックネームが未登録です。今すぐ登録できます！")
        if st.button("プロフィール登録に進む"):
            st.session_state.page = "profile"
            st.rerun()
        # ページ管理
        if st.session_state.page == "profile":
            profile_page()
            st.stop()
    else:
        # メインページ（drillページなど）へ遷移
        drill_main()
