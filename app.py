import streamlit as st
from auth import login_page, signup_page
from pages.drill_page import drill_main
from profile_page import profile_page  # ← プロフィール編集ページ

# ── セッション初期化 ───────────────────────────────
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("page", "login")  # login / signup / home / profile
st.session_state.setdefault("username", None)  # ニックネーム

# ── サイドバー（ログイン後のみ） ───────────────────
if st.session_state.user_id:
    with st.sidebar:
        st.title("メニュー")
        if st.button("プロフィール編集", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
        st.divider()
        st.caption(f"👤 {st.session_state.username or 'ユーザー'}")

# ── 認証前（ログイン／新規登録） ───────────────────
if not st.session_state.user_id:
    if st.session_state.page == "signup":
        signup_page()
    else:  # "login"
        login_page()
    st.stop()

# ── 認証後：プロフィール確認 → 画面振り分け ────────
if not st.session_state.username and st.session_state.page != "profile":
    # ニックネーム未登録なら強制プロフィール編集へ
    st.session_state.page = "profile"
    st.rerun()

# ページ表示
if st.session_state.page == "profile":
    profile_page()
else:  # "home"
    drill_main()
