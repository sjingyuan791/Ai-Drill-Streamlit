import streamlit as st
from supabase import create_client, Client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


def save_answer_log(
    user_id,
    subject,
    topic,
    question,
    selected_choice,
    is_correct,
    level=None,
    distractor_reason=None,
):
    data = {
        "user_id": user_id,
        "subject": subject,
        "topic": topic,
        "question": question,
        "selected_choice": selected_choice,
        "is_correct": is_correct,
        "level": level,
        "distractor_reason": distractor_reason,
    }
    supabase.table("answer_log").insert(data).execute()


def get_user_answer_stats(user_id, subject=None, topic=None):
    query = supabase.table("answer_log").select("*").eq("user_id", user_id)
    if subject:
        query = query.eq("subject", subject)
    if topic:
        query = query.eq("topic", topic)
    response = query.execute()
    return response.data


def get_user_profile(user_id):
    response = supabase.table("user").select("*").eq("id", user_id).single().execute()
    return response.data


def update_user_level(user_id, level):
    supabase.table("user").update({"level": level}).eq("id", user_id).execute()
