import streamlit as st
from openai import OpenAI
from supabase import create_client, Client
import json

# === Supabase接続 ===
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="AIドリル for 中学生", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- キャラクター設定 ---
character_profiles = {
    "さくら先生": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/sakura.png",
        "style": "優しく元気いっぱい、語尾に『〜だよ♪』『すごいねっ！』など",
        "persona": "陽気で元気いっぱいな女子先生。やさしく丁寧に励ます口調。",
    },
    "レイ先生": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/rei.png",
        "style": "冷静で的確、時々ツンデレ風。『…べ、別にお前のためじゃない』等",
        "persona": "クールでツンデレな男子先生。ぶっきらぼうだが分かりやすく説明。",
    },
}

# --- ページ管理 ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "qa_data" not in st.session_state:
    st.session_state.qa_data = None
if "explanation_loop" not in st.session_state:
    st.session_state.explanation_loop = 0
if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False
if "auto_next" not in st.session_state:
    st.session_state.auto_next = False


# === Supabase認証関連 ===
def create_user(username, password):
    data = {"username": username, "password": password}
    res = supabase.table("user").insert(data).execute()
    if res.data:
        return True
    return False


def check_login(username, password):
    res = (
        supabase.table("user")
        .select("*")
        .eq("username", username)
        .eq("password", password)
        .execute()
    )
    if res.data:
        return res.data[0]["id"]  # user_id
    return None


def get_username(user_id):
    res = supabase.table("user").select("username").eq("id", user_id).execute()
    if res.data:
        return res.data[0]["username"]
    return ""


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


# --- ログイン・新規登録画面 ---
if st.session_state.user_id is None:
    if st.session_state.page == "login":
        st.header("ログイン")
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            user_id = check_login(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.success("ログイン成功！")
                st.rerun()
            else:
                st.error("ログイン失敗。ユーザー名またはパスワードが違います。")
        if st.button("新規登録はこちら"):
            st.session_state.page = "signup"
            st.rerun()

    elif st.session_state.page == "signup":
        st.header("新規登録")
        new_username = st.text_input("新しいユーザー名")
        new_password = st.text_input("新しいパスワード", type="password")
        if st.button("登録"):
            if create_user(new_username, new_password):
                st.success("登録成功！そのままログインしてください。")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("そのユーザー名はすでに使われています。")
        if st.button("ログイン画面へ戻る"):
            st.session_state.page = "login"
            st.rerun()
    st.stop()

# --- 本編 ---
st.write(f"こんにちは、{get_username(st.session_state.user_id)} さん！")

character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
st.image(
    character_profiles[character]["image_url"],
    caption=character,
    use_container_width=True,
)
subjects = {
    "国語": ["漢字・語句", "文法・品詞", "説明文読解", "文学的文章読解"],
    "数学": [
        "正の数と負の数",
        "文字式",
        "一次方程式",
        "比例と反比例",
        "平面図形",
        "空間図形",
        "資料の活用",
    ],
    "英語": ["be動詞", "一般動詞", "疑問詞", "助動詞can", "現在進行形", "代名詞"],
    "社会": [
        "日本の位置と領域",
        "世界の気候",
        "旧石器〜弥生時代",
        "古代国家",
        "中世〜近世",
        "公民：憲法と経済",
    ],
    "理科": ["植物", "水溶液", "光と音", "生物の分類"],
}
subject = st.selectbox("教科をえらぼう！", list(subjects.keys()))
topic = st.selectbox("単元をえらぼう！", subjects[subject])
level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"])


# --------- 自動出題処理 ---------
def generate_new_question():
    prompt = f"""
あなたは日本の中学1年生向け学習支援AI「{character}」です。
キャラクター性：{character_profiles[character]['persona']}
次の条件で、【問題】【選択肢4つ】【正解】【理由の解説】に加えて、必ず【正解時コメント】【不正解時コメント】もキャラらしく日本語で付けて、以下のJSON形式だけで返してください。

教科: {subject}
単元: {topic}
難易度: {level}
キャラ口調: {character_profiles[character]['style']}

# 出力形式（例を改変して使うこと）:
{{
  "question": "...",
  "choices": ["...","...","...","..."],
  "answer": "...",
  "explanation": "...",
  "correct_message": "...",
  "incorrect_message": "..."
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        data = json.loads(content[json_start:json_end])
        st.session_state.qa_data = data
        st.session_state.explanation_loop = 0
        st.session_state.show_explanation = False
    except Exception as e:
        st.error(f"問題取得に失敗しました: {str(e)}")


if st.session_state.auto_next:
    with st.spinner("次の問題を用意中…"):
        generate_new_question()
        st.session_state.auto_next = False
    st.rerun()

if st.button("問題を出して！"):
    with st.spinner("先生が考え中…"):
        generate_new_question()

if st.session_state.qa_data:
    qd = st.session_state.qa_data
    st.markdown(f"### 📝 {character}からの問題：")
    st.markdown(f"**{qd['question']}**")
    choice = st.radio(
        "こたえをえらんでね：", qd["choices"], key=f"choices_{qd['question']}"
    )

    if st.button("こたえあわせ！"):
        is_correct = int(choice == qd["answer"])
        save_answer_log(
            st.session_state.user_id,
            subject,
            topic,
            qd["question"],
            choice,
            is_correct,
        )
        if is_correct:
            st.success(qd.get("correct_message", "🎉 正解だよ！すごいねっ！"))
        else:
            st.error(
                qd.get("incorrect_message", f"🙈 残念…正解は「{qd['answer']}」だよ〜")
            )
        st.info(f"🧠 解説：{qd['explanation']}")
        st.session_state.show_explanation = True

    if st.session_state.show_explanation:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("まだよくわからない…もう一度説明して"):
                st.session_state.explanation_loop += 1
                loop_prompt = f"""
あなたは日本の中学1年生向け学習支援AI「{character}」です。
キャラクター性：{character_profiles[character]['persona']}
いまから出す解説を、{st.session_state.explanation_loop+1}回目の説明として、小学生にも分かるようにキャラらしい優しい口調で言い換えてください。

【もとの解説】
{qd['explanation']}
"""
                try:
                    loop_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": loop_prompt}],
                    )
                    loop_expl = loop_response.choices[0].message.content.strip()
                    st.warning(f"🧠 もっとやさしい解説：\n{loop_expl}")
                    st.session_state.qa_data["explanation"] = loop_expl
                except Exception as e:
                    st.warning("もう少しうまく説明できなかったみたい…")
        with col2:
            if st.button("次の問題に進む"):
                st.session_state.qa_data = None
                st.session_state.show_explanation = False
                st.session_state.auto_next = True
                st.rerun()

if not st.session_state.qa_data:
    st.markdown(
        '👆 上のメニューから好きな教科・単元・先生をえらんで、"問題を出して！"ボタンを押してね！'
    )
