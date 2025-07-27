import streamlit as st
from supabase import create_client, Client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


def save_answer_log(user_id, subject, topic, question, selected_choice, is_correct):
    data = {
        "user_id": user_id,
        "subject": subject,
        "topic": topic,
        "question": question,
        "selected_choice": selected_choice,
        "is_correct": is_correct,
    }
    supabase.table("answer_log").insert(data).execute()


# もし履歴一覧・他ユーザ情報取得など追加したい場合はここに関数を追記
