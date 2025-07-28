import streamlit as st
from db import supabase


def profile_page():
    st.header("プロフィール作成・編集")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("ログインしてください。")
        return

    # 現在のユーザー情報取得
    user_row = supabase.table("user").select("*").eq("id", user_id).single().execute()
    current_name = user_row.data.get("username", "")

    new_name = st.text_input("ニックネーム（好きな名前）", value=current_name or "")

    if st.button("保存"):
        try:
            supabase.table("user").update({"username": new_name}).eq(
                "id", user_id
            ).execute()
            st.success("プロフィールが更新されました！")
            st.session_state["username"] = new_name  # 即時反映
            # --- ドリル画面へ自動遷移 ---
            st.switch_page("pages/drill_page.py")
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

    if st.button("戻る"):
        st.session_state.page = "home"  # 適切なトップページ等に
        st.rerun()
