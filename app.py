# 📘 Streamlit版：中学生向けAIドリルアプリ（キャラ口調反映＋解説ループ）

import streamlit as st
import openai
import json

st.set_page_config(page_title="AIドリル for 中学生", layout="centered")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🧑‍🏫 AI先生プロファイル設定
character_profiles = {
    "さくら先生": {
        "persona": "陽気で元気いっぱいな女子先生。やさしく丁寧に、語尾に「〜だよっ」「〜ね！」をつける。生徒を励ますのが得意。",
        "image_url": "https://example.com/sakura.png",
    },
    "レイ先生": {
        "persona": "クールでツンデレな男子先生。理論的でぶっきらぼうだけど、実は生徒思い。語尾はドライだが、説明は的確で優しい。",
        "image_url": "https://example.com/rei.png",
    },
}

character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
st.image(
    character_profiles[character]["image_url"], caption=character, use_column_width=True
)

# 教科・単元・難易度の選択
subject = st.selectbox("教科をえらぼう！", ["国語", "数学", "英語", "社会", "理科"])
topics = {
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
        "世界の気候と人々の生活",
        "旧石器〜弥生時代",
        "古代国家と東アジア",
        "中世〜近世の歴史",
        "公民：憲法と経済の基本",
    ],
    "理科": [
        "植物の構成と分類",
        "水溶液の性質",
        "光と音の性質",
        "身近な生物の観察と分類",
    ],
}
topic = st.selectbox("単元をえらぼう！", topics.get(subject, []))
level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"])

# セッション管理
if "drill" not in st.session_state:
    st.session_state["drill"] = None
if "explanation" not in st.session_state:
    st.session_state["explanation"] = None
if "explanation_loop" not in st.session_state:
    st.session_state["explanation_loop"] = 0


# 🎓 解説のやさしく言い換え
def get_easier_explanation(explanation, character):
    persona = character_profiles[character]["persona"]
    prompt = f"""
あなたは中学1年生向け学習支援AI「{character}」です。
キャラクターの性格：{persona}
以下の解説をさらに分かりやすく、小学生でも理解できるように例えや優しい言葉を使ってキャラの口調で再説明してください。
【もとの解説】
{explanation}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# 🎲 問題出題
if st.button("問題を出して！"):
    with st.spinner("先生が一生懸命考え中... ✍️"):
        persona = character_profiles[character]["persona"]
        prompt = f"""
あなたは中学1年生向け学習支援AI「{character}」です。
キャラクターの性格：{persona}
以下の条件で1問、キャラらしい口調で、選択式ドリル問題をJSON形式で出してください。

教科: {subject}
単元: {topic}
難易度: {level}

形式：
{{"question":"...", "choices": [...], "answer":"...", "explanation":"..."}}
"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            json_str = content[content.find("{") : content.rfind("}") + 1]
            data = json.loads(json_str)
            st.session_state["drill"] = data
            st.session_state["explanation"] = data["explanation"]
            st.session_state["explanation_loop"] = 0
        except Exception as e:
            st.error(f"エラー: {str(e)}")

# 📝 問題・解説表示と解説ループ
if st.session_state["drill"]:
    data = st.session_state["drill"]
    st.markdown(f"### 📝 {character}からの問題：")
    st.markdown(f"**{data['question']}**")
    choice = st.radio("こたえをえらんでね：", data["choices"], key="choice")

    if st.button("こたえあわせ！"):
        if choice == data["answer"]:
            st.success(
                "🎉 正解だよっ！すごいすごいっ💮"
                if character == "さくら先生"
                else "…まあ、悪くないな（照）"
            )
        else:
            st.error(
                f"🙈 ざんねんっ！正解は「{data['answer']}」だったよ〜"
                if character == "さくら先生"
                else f"違う。正解は「{data['answer']}」だ。"
            )
        st.session_state["show_explanation"] = True

    if st.session_state.get("show_explanation", False):
        st.info(f"🧠 {character}の解説：{st.session_state['explanation']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("分かった！"):
                st.success(
                    "じゃあ、次いこっか！🌟"
                    if character == "さくら先生"
                    else "よし、次だ。"
                )
                st.session_state["drill"] = None
                st.session_state["show_explanation"] = False
        with col2:
            if st.button("分からない…もっとやさしく"):
                easier = get_easier_explanation(
                    st.session_state["explanation"], character
                )
                st.session_state["explanation"] = easier
                st.session_state["explanation_loop"] += 1
                st.experimental_rerun()

# 案内
if not st.session_state["drill"]:
    st.markdown("👆 教科と単元と先生をえらんで「問題を出して！」を押してみよう！")
