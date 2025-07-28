import streamlit as st
from db import supabase

def login_page():
    st.header("ログイン")
    st.markdown("🔰 **はじめての人は『新規登録』ボタンから登録してね！**")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ログイン"):
            try:
                res = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state.user_id = res.user.id
                st.success("ログイン成功！")
                st.rerun()
            except Exception as e:
                st.error("ログインできませんでした。")
                st.info("""
新規登録した場合は、必ずメールを確認して「Confirm your mail」という青いボタンを押してから、もう一度ログインしてね！
もしメールが届かない場合は迷惑メールフォルダもチェック！
                """)
    with col2:
        if st.button("新規登録はこちら"):
            st.session_state.page = "signup"
            st.rerun()

def signup_page():
    st.header("新規登録")
    st.markdown("""
### スタートガイド
1. 下のフォームにメールアドレスと好きなパスワードを入力して「登録」
2. メールが届いたら、青いボタン「Confirm your mail」を押そう
3. その後、もう一度この画面でログインしてね！

※ メールが届かないときは迷惑メールフォルダも見てね。
""")
    email = st.text_input("新しいメールアドレス")
    password = st.text_input("新しいパスワード", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("登録"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("登録ができました！メールの青いボタンを押してから、もう一度ログインしてください。")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                st.error(f"登録失敗: {e}")
    with col2:
        if st.button("ログイン画面へ戻る"):
            st.session_state.page = "login"
            st.rerun()
