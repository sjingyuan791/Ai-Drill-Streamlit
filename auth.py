import streamlit as st
from db import supabase


def login_page():
    st.header("ログイン")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        try:
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            st.session_state.user_id = res.user.id
            st.success("ログイン成功！")
            st.rerun()
        except Exception as e:
            st.error(f"ログイン失敗: {e}")
    if st.button("新規登録はこちら"):
        st.session_state.page = "signup"
        st.rerun()


def signup_page():
    st.header("新規登録")
    email = st.text_input("新しいメールアドレス")
    password = st.text_input("新しいパスワード", type="password")
    if st.button("登録"):
        try:
            supabase.auth.sign_up({"email": email, "password": password})
            st.success("登録成功！そのままログインしてください。")
            st.session_state.page = "login"
            st.rerun()
        except Exception as e:
            st.error(f"登録失敗: {e}")
    if st.button("ログイン画面へ戻る"):
        st.session_state.page = "login"
        st.rerun()
