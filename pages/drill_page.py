import streamlit as st
import json
from openai import OpenAI
from db import save_answer_log
from ui_components import show_character_avatar

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# キャラクタープロファイル
character_profiles = {
    "さくら先生": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/sakura.png",
        "style": "優しく元気いっぱい、語尾に『〜だよ♪』など",
        "persona": "陽気で元気いっぱいな女子先生。やさしく丁寧に励ます口調。",
    },
    "レイ先生": {
        "image_url": "https://raw.githubusercontent.com/sjingyuan791/Ai-Drill-Streamlit/main/rei.png",
        "style": "冷静で的確、時々ツンデレ風。",
        "persona": "クールでツンデレな男子先生。",
    },
}

# 教科ごとの単元
subjects = {
    "国語": ["漢字", "文法", "読解", "文学史"],
    "数学": ["整数", "小数・分数", "方程式", "図形", "関数"],
    "英語": ["文法", "単語", "長文読解"],
    "理科": ["生物", "化学", "物理", "地学"],
    "社会": ["地理", "歴史", "公民"],
}


def drill_main():
    # セッション管理
    for key, val in {
        "qa_data": None,
        "explanation_loop": 0,
        "show_explanation": False,
        "auto_next": False,
        "selected_choice": None,
        "answered": False,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

    st.markdown("### AIドリルで勉強しよう！")
    st.write(f"こんにちは、ユーザーID: {st.session_state.user_id} さん！")

    # 先生・教科・単元・難易度
    character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
    show_character_avatar(character, character_profiles)
    subject = st.selectbox("教科をえらぼう！", list(subjects.keys()))
    topic = st.selectbox("単元をえらぼう！", subjects[subject])
    level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"])

    # 問題生成ボタン
    if st.button("新しい問題を出す", key="generate_q"):
        st.session_state.qa_data = None  # 直前の問題リセット
        st.session_state.answered = False
        st.session_state.selected_choice = None
        st.session_state.show_explanation = False
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
        with st.spinner("AIが問題を考えています..."):
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
            except Exception as e:
                st.error(f"問題取得に失敗しました: {str(e)}")
                st.stop()

    qa_data = st.session_state.qa_data
    if qa_data:
        st.markdown(f"#### 問題: {qa_data['question']}")
        choices = qa_data["choices"]
        st.session_state.selected_choice = st.radio(
            "選択肢から1つ選んでください",
            choices,
            index=(
                None
                if not st.session_state.selected_choice
                else choices.index(st.session_state.selected_choice)
            ),
            disabled=st.session_state.answered,
        )

        if not st.session_state.answered:
            if st.button("答え合わせ", key="answer_btn"):
                st.session_state.answered = True
                user_answer = st.session_state.selected_choice
                correct = user_answer == qa_data["answer"]
                st.session_state.show_explanation = True

                # 保存
                save_answer_log(
                    st.session_state.user_id,
                    subject,
                    topic,
                    qa_data["question"],
                    user_answer,
                    int(correct),
                )
                if correct:
                    st.success(
                        f"正解！ {qa_data.get('correct_message', 'よくできました！')}"
                    )
                else:
                    st.error(
                        f"不正解... {qa_data.get('incorrect_message', 'がんばれ！')}"
                    )
        else:
            # 結果・解説表示
            correct = st.session_state.selected_choice == qa_data["answer"]
            if correct:
                st.success(
                    f"正解！ {qa_data.get('correct_message', 'よくできました！')}"
                )
            else:
                st.error(f"不正解... {qa_data.get('incorrect_message', 'がんばれ！')}")
            st.info(f"【正解】{qa_data['answer']}")
            if st.session_state.show_explanation:
                st.markdown("#### 解説")
                st.write(qa_data.get("explanation", ""))

        if st.session_state.answered and st.button("次の問題へ", key="next_q"):
            st.session_state.qa_data = None
            st.session_state.answered = False
            st.session_state.selected_choice = None
            st.session_state.show_explanation = False
            st.rerun()

    else:
        st.info("「新しい問題を出す」ボタンを押してスタート！")
