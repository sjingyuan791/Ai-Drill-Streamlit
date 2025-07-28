import streamlit as st
from db import supabase

def login_page():
    st.header("ログイン")
    st.markdown("🔰 **はじめての方は「新規登録」ボタンから始めてね！**")
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
                # ユーザー情報取得
                user_row = (
                    supabase.table("user")
                    .select("*")
                    .eq("id", res.user.id)
                    .single()
                    .execute()
                )
                st.session_state.username = user_row.data.get("username", "")
                # プロフィール未登録の場合の案内
                if not st.session_state.username:
                    st.info("プロフィール（ニックネーム）は未設定です。後からいつでも設定できます。")
                st.success(
                    f"ログイン成功！ようこそ、{st.session_state.username or 'ユーザー'} さん"
                )
                st.rerun()
            except Exception as e:
                st.error("ログインできませんでした。")
                st.info(
                    """
新規登録した場合は、必ずメールを確認して「Confirm your mail」という青いボタンを押してから、もう一度ログインしてね！
メールが届かないときは迷惑メールフォルダも見てね。
"""
                )
    with col2:
        if st.button("新規登録はこちら"):
            st.session_state.page = "signup"
            st.rerun()

def signup_page():
    st.header("新規登録（無料）")
    st.markdown(
        """
### スタートガイド
1. 下のフォームにメールアドレス・パスワードを入力して「登録」
2. 登録後、メールが届くので「Confirm your mail」ボタンを必ず押してね
3. その後、この画面でログイン！

※メールが届かないときは迷惑メールフォルダもチェック！
"""
    )
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("登録"):
            if not email or not password:
                st.warning("すべての項目を入力してください")
            else:
                try:
                    # サインアップ
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success(
                        "登録ができました！メールの青いボタンを押してから、もう一度ログインしてください。"
                    )
                    st.session_state.page = "login"
                    st.rerun()
                except Exception as e:
                    st.error(f"登録失敗: {e}")
    with col2:
        if st.button("ログイン画面へ戻る"):
            st.session_state.page = "login"
            st.rerun()
