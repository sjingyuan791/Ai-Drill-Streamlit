import streamlit as st
from db import supabase


def profile_page() -> None:
    """ニックネームを登録・編集するページ（全ページ共通で呼び出し可能）"""
    st.header("プロフィール作成・編集")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("ログインしてください。")
        return

    # ── 現在のユーザー名取得 ─────────────────────
    resp = (
        supabase.table("user").select("username").eq("id", user_id).single().execute()
    )
    current_name = resp.data.get("username", "")

    # ── 入力フォーム ─────────────────────────────
    new_name = st.text_input("ニックネーム（好きな名前）", value=current_name or "")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("保存", use_container_width=True):
            try:
                supabase.table("user").update({"username": new_name}).eq(
                    "id", user_id
                ).execute()
                st.session_state.username = new_name  # 即時反映
                st.success("プロフィールを更新しました！")
                st.session_state.page = "home"  # ← ホームへ戻す
                st.rerun()
            except Exception as e:
                st.error(f"更新に失敗しました: {e}")

    with col2:
        if st.button("キャンセル", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
