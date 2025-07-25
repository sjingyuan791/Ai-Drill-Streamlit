# 📘 中学生向けAIドリルアプリ（新OpenAI API対応＋キャラ別解説＋画像対応）

import streamlit as st
from openai import OpenAI
import json

st.set_page_config(page_title="AIドリル for 中学生", layout="centered")

# 🔑 OpenAI APIキーの読み込み
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🎭 キャラクター設定
character_profiles = {
    "陽気な萌え系女子先生（さくら先生）": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/sakura.png",
        "style": "優しく、元気いっぱいで励ますように、語尾に「〜だよ♪」「すごいねっ！」など",
        "persona": "陽気で元気いっぱいな女子先生。やさしく丁寧に、語尾に「〜だよっ」「〜ね！」をつける。生徒を励ますのが得意。"
    },
    "クールなツンデレ男子先生（レイ先生）": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/rei.png",
        "style": "冷静で的確、たまに照れながら褒めるように、「べ、別にお前のためじゃないけどな…」風",
        "persona": "クールでツンデレな男子先生。理論的でぶっきらぼうだけど、実は生徒思い。語尾はドライだが、説明は的確で優しい。"
    },
}

# 🧑‍🏫 先生選択＋画像表示
character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
st.image(
    character_profiles[character]["image_url"],
    caption=character,
    use_container_width=True
)

# 📘 教科と単元
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

# 🧠 セッションステートで保持
if "qa_data" not in st.session_state:
    st.session_state.qa_data = None
if "explanation_loop" not in st.session_state:
    st.session_state.explanation_loop = 0
if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False

# 🎲 問題出題
if st.button("問題を出して！"):
    with st.spinner("先生が考え中…"):
        prompt = f"""
あなたは中学1年生向けの{character}です。
キャラクターの性格：{character_profiles[character]['persona']}
以下の条件に基づいて、選択式ドリル問題を1問作ってください。

教科: {subject}
単元: {topic}
難易度: {level}
キャラ口調: {character_profiles[character]['style']}

返答形式は以下のJSON形式：
{{
  "question": "...",
  "choices": ["...","...","...","..."],
  "answer": "...",
  "explanation": "..."
}}
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
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

# 📝 出題・回答
if st.session_state.qa_data:
    st.markdown(f"### 📝 {character}からの問題：")
    st.markdown(f"**{st.session_state.qa_data['question']}**")
    choice = st.radio("こたえをえらんでね：", st.session_state.qa_data["choices"])

    if st.button("こたえあわせ！"):
        if choice == st.session_state.qa_data["answer"]:
            st.success(
                "🎉 正解だよ！すごいねっ！"
                if "さくら" in character
                else "ふん、やればできるじゃないか"
            )
        else:
            st.error(
                f"🙈 残念…正解は「{st.session_state.qa_data['answer']}」だよ〜"
                if "さくら" in character
                else f"……違う。正解は「{st.session_state.qa_data['answer']}」だ"
            )
        st.info(f"🧠 解説：{st.session_state.qa_data['explanation']}")
        st.session_state.show_explanation = True

    # ✅ 解説が分かったか確認（再解説ボタン）
    if st.session_state.show_explanation:
        if st.button("まだよくわからない…もう一度説明して"):
            st.session_state.explanation_loop += 1
            loop_prompt = f"""
中学1年生に向けて以下の内容を、もっと分かりやすく{st.session_state.explanation_loop}回目として解説してください。
キャラ口調: {character_profiles[character]['style']}
キャラクターの性格：{character_profiles[character]['persona']}
解説: {st.session_state.qa_data['explanation']}
"""
            try:
                loop_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": loop_prompt}]
                )
                loop_expl = loop_response.choices[0].message.content.strip()
                st.warning(f"🧠 もっとやさしい解説：\n{loop_expl}")
                # 追加解説もqa_data["explanation"]に一時保存可能
                st.session_state.qa_data['explanation'] = loop_expl
            except Exception as e:
                st.warning("もう少しうまく説明できなかったみたい…")

# 🎈 案内
if not st.session_state.qa_data:
    st.markdown(
        '👆 上のメニューから好きな教科・単元・先生をえらんで、"問題を出して！"ボタンを押してね！'
    )
