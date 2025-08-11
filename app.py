import streamlit as st
from auth import login_page, signup_page
from pages.drill_page import drill_main
from profile_page import profile_page
from pages.dashboard_page import dashboard_main

# ── セッション初期化 ─────────────────────────────
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("page", "dashboard")  # dashboard / drill / profile / login / signup
st.session_state.setdefault("username", None)
# 改修で追加（適応難易度・連続出題）
st.session_state.setdefault("recent_corrects", [])  # 直近正誤（True/False）の履歴（最大10件）
st.session_state.setdefault("auto_next", False)     # 連続出題モード

# ── サイドバー（ログイン後のみ） ─────────────────
if st.session_state.user_id:
    with st.sidebar:
        st.title("メニュー")
        if st.button("ダッシュボード", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("学習ドリル", use_container_width=True):
            st.session_state.page = "drill"
            st.rerun()
        if st.button("プロフィール編集", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
        st.divider()
        # 連続出題モード（全体設定）
        st.session_state.auto_next = st.toggle(
            "連続出題モード", value=st.session_state.get("auto_next", False)
        )
        st.caption(f"👤 {st.session_state.username or 'ユーザー'}")

# ── 認証前（ログイン／新規登録） ───────────────────
if not st.session_state.user_id:
    if st.session_state.page == "signup":
        signup_page()
    else:  # "login"
        login_page()
    st.stop()

# ── ニックネーム未登録 → プロフィールを先に ───────────
if not st.session_state.username and st.session_state.page != "profile":
    st.session_state.page = "profile"
    st.rerun()

# ── メイン画面：ページ状態で表示を切替 ───────────────
if st.session_state.page == "dashboard":
    dashboard_main()
elif st.session_state.page == "drill":
    drill_main()
elif st.session_state.page == "profile":
    profile_page()
else:
    dashboard_main()
