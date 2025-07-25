import streamlit as st
from openai import OpenAI
import json

st.set_page_config(page_title="AIドリル for 中学生", layout="centered")

# OpenAIクライアント
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# キャラクタープロファイル
character_profiles = {
    "陽気な萌え系女子先生（さくら先生）": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/sakura.png",
        "style": "優しく元気いっぱい、語尾に『〜だよ♪』『すごいねっ！』など",
        "persona": "陽気で元気いっぱいな女子先生。やさしく丁寧に励ます口調。",
    },
    "クールなツンデレ男子先生（レイ先生）": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/rei.png",
        "style": "冷静で的確、時々ツンデレ風。『…べ、別にお前のためじゃない』等",
        "persona": "クールでツンデレな男子先生。ぶっきらぼうだが分かりやすく説明。",
    },
}

# UI: 先生・教科・単元・難易度
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

# セッション
if "qa_data" not in st.session_state:
    st.session_state.qa_data = None
if "explanation_loop" not in st.session_state:
    st.session_state.explanation_loop = 0
if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False

# 出題プロンプト
if st.button("問題を出して！"):
    with st.spinner("先生が考え中…"):
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

# 出題・解答判定
if st.session_state.qa_data:
    qd = st.session_state.qa_data
    st.markdown(f"### 📝 {character}からの問題：")
    st.markdown(f"**{qd['question']}**")
    choice = st.radio("こたえをえらんでね：", qd["choices"], key=f"choices_{qd['question']}")

    if st.button("こたえあわせ！"):
        if choice == qd["answer"]:
            st.success(qd.get("correct_message", "🎉 正解だよ！すごいねっ！"))
        else:
            st.error(qd.get("incorrect_message", f"🙈 残念…正解は「{qd['answer']}」だよ〜"))
        st.info(f"🧠 解説：{qd['explanation']}")
        st.session_state.show_explanation = True

    # さらに分かりやすい解説
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
                st.experimental_rerun()

# 初期ガイダンス
if not st.session_state.qa_data:
    st.markdown(
        '👆 上のメニューから好きな教科・単元・先生をえらんで、"問題を出して！"ボタンを押してね！'
    )
