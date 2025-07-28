import streamlit as st
from auth import login_page, signup_page
from pages.drill_page import drill_main
from profile_page import profile_page
from pages.dashboard import dashboard_main  # ← 新規作成（後述）

# セッション初期化
st.session_state.setdefault("user_id", None)
st.session_state.setdefault(
    "page", "dashboard"
)  # dashboard / drill / profile / login / signup
st.session_state.setdefault("username", None)

# ── サイドバー（ログイン後のみ） ─────────────
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
        st.caption(f"👤 {st.session_state.username or 'ユーザー'}")

# ── 認証前（ログイン／新規登録） ──────────────
if not st.session_state.user_id:
    if st.session_state.page == "signup":
        signup_page()
    else:  # "login"
        login_page()
    st.stop()

# ── ニックネーム未登録 → プロフィール登録を強制 ──
if not st.session_state.username and st.session_state.page != "profile":
    st.session_state.page = "profile"
    st.rerun()

# ── メイン画面：ページ状態で表示を切り替え ──────
if st.session_state.page == "dashboard":
    dashboard_main()  # ← ダッシュボード（学習状況・苦手分析）
elif st.session_state.page == "drill":
    drill_main()
elif st.session_state.page == "profile":
    profile_page()
else:
    dashboard_main()
