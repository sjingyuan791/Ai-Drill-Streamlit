# 📘 Streamlit版：中学生向けAIドリルアプリ（解説の再説明ループ機能付き）

import streamlit as st
import openai
import json

st.set_page_config(page_title="AIドリル for 中学生", layout="centered")

# 🔑 OpenAI APIキー
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🧑‍🏫 AI先生のキャラクターを選択
character = st.selectbox(
    "AI先生を選んでね",
    ["さくら先生", "レイ先生"],
)

# 🎨 先生の画像表示
if character == "陽気な萌え系女子先生（さくら先生）":
    st.image(
        "https://example.com/sakura.png", caption="さくら先生", use_column_width=True
    )
elif character == "クールなツンデレ男子先生（レイ先生）":
    st.image("https://example.com/rei.png", caption="レイ先生", use_column_width=True)

# 👨‍🎓 教科選択
subject = st.selectbox("教科をえらぼう！", ["国語", "数学", "英語", "社会", "理科"])

# 📖 単元選択（教科ごとに異なる単元）
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

# 🎚 難易度選択
level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"])

# 🌀 セッションステートで状態を管理
if "drill" not in st.session_state:
    st.session_state["drill"] = None
if "explanation" not in st.session_state:
    st.session_state["explanation"] = None
if "explanation_loop" not in st.session_state:
    st.session_state["explanation_loop"] = 0


# 👩‍🏫 解説をさらに分かりやすくする関数
def get_easier_explanation(explanation, character):
    prompt = f"""
あなたは日本の中学1年生向け学習支援AI「{character}」です。
以下の解説を、さらに分かりやすく、例えや具体例も使いながら、小学生でも必ず理解できるレベルでやさしく言い換えてください。
【もとの解説】
{explanation}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# 🎲 問題を出す
if st.button("問題を出して！"):
    with st.spinner("先生が一生懸命考え中... ✍️"):
        prompt = f"あなたは中学1年生向けの{character}です。以下の条件で1問、選択式ドリル問題を出してください：\n"
        prompt += f"教科: {subject}\n単元: {topic}\n難易度: {level}\n"
        prompt += 'JSON形式で以下のように返してください：{"question":"...", "choices": [...], "answer":"...", "explanation":"..."}'

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
            data = json.loads(json_str)

            st.session_state["drill"] = data
            st.session_state["explanation"] = data["explanation"]
            st.session_state["explanation_loop"] = 0

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

# 問題と解説表示
if st.session_state["drill"]:
    data = st.session_state["drill"]
    st.markdown(f"### 📝 {character}からの問題：")
    st.markdown(f"**{data['question']}**")
    choice = st.radio(
        "こたえをえらんでね：", data["choices"], key=f"choices_{data['question']}"
    )
    if st.button("こたえあわせ！", key=f"check_{data['question']}"):
        if choice == data["answer"]:
            st.success("🎉 正解だよ！えらいえらいっ💮")
        else:
            st.error(f"🙈 ざんねんっ！正解は「{data['answer']}」だよ〜")
        st.session_state["show_explanation"] = True

    # 解説を表示・分かった？分からない？ボタン
    if st.session_state.get("show_explanation", False):
        st.info(f"🧠 {character}の解説：{st.session_state['explanation']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "分かった！", key=f"understand_{st.session_state['explanation_loop']}"
            ):
                st.success("よかった！次の問題に進もう！")
                st.session_state["drill"] = None
                st.session_state["show_explanation"] = False
        with col2:
            if st.button(
                "分からない…もっとやさしく",
                key=f"easier_{st.session_state['explanation_loop']}",
            ):
                easier = get_easier_explanation(
                    st.session_state["explanation"], character
                )
                st.session_state["explanation"] = easier
                st.session_state["explanation_loop"] += 1
                st.experimental_rerun()

# 🎈 案内メッセージ
if not st.session_state["drill"]:
    st.markdown(
        '👆 上のメニューから好きな教科・単元・先生をえらんで、"問題を出して！"ボタンを押してね！'
    )
