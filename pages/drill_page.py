import streamlit as st
import json
from openai import OpenAI
from db import save_answer_log, get_user_answer_stats
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

# 学習指導要領に準拠した中1の単元
subjects = {
    "国語": [
        "物語文の読解",
        "説明文・要旨把握",
        "言葉の意味・漢字",
        "品詞・活用",
        "古文・漢文の基礎",
        "俳句・短歌",
    ],
    "数学": [
        "正負の数",
        "文字式",
        "一次方程式",
        "比例・反比例",
        "平面図形",
        "空間図形",
        "資料の整理",
    ],
    "英語": [
        "be動詞・一般動詞",
        "命令文",
        "疑問詞",
        "助動詞can",
        "現在進行形",
        "代名詞",
        "三単現s",
    ],
    "理科": [
        "植物の分類",
        "動物の分類",
        "身のまわりの物質",
        "光と音",
        "大地の変化",
        "大気と水",
    ],
    "社会": [
        "世界のすがた",
        "日本の国土",
        "古代の日本",
        "中世の日本",
        "現代社会の基礎",
    ],
}


def calc_topic_weakness(user_id, subject):
    # ユーザーの正答率が80%未満の単元をおすすめ順に（3問以上解答のみ集計）
    stats = get_user_answer_stats(user_id, subject)
    topic_stats = {}
    for row in stats:
        t = row["topic"]
        if t not in topic_stats:
            topic_stats[t] = {"total": 0, "correct": 0}
        topic_stats[t]["total"] += 1
        topic_stats[t]["correct"] += row["is_correct"]
    result = []
    for t, d in topic_stats.items():
        if d["total"] >= 3:
            acc = d["correct"] / d["total"]
            result.append((t, acc))
    # 正答率が80%未満を優先、昇順
    result = sorted([r for r in result if r[1] < 0.8], key=lambda x: x[1])
    weak_topics = [r[0] for r in result]
    return weak_topics


def drill_main():
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
    display_name = (
        st.session_state.get("username") or f"ユーザーID: {st.session_state.user_id}"
    )
    st.write(f"こんにちは、{display_name} さん！")

    character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
    show_character_avatar(character, character_profiles)
    subject = st.selectbox("教科をえらぼう！", list(subjects.keys()))

    weak_topics = calc_topic_weakness(st.session_state.user_id, subject)
    all_topics = weak_topics + [t for t in subjects[subject] if t not in weak_topics]
    topic = st.selectbox("単元（AIおすすめ順）", all_topics)
    if weak_topics:
        st.info(f"おすすめ: {'・'.join(weak_topics)}（正答率80％未満）")
    level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"])

    # 問題生成プロンプト（学習指導要領＆入試品質、誤答理由も出力させる）
    if st.button("新しい問題を出す", key="generate_q"):
        st.session_state.qa_data = None
        st.session_state.answered = False
        st.session_state.selected_choice = None
        st.session_state.show_explanation = False
        prompt = f"""
あなたは日本の中学校教員です。
令和の学習指導要領・全国公立高校入試の頻出問題・定期テスト・検定教科書の例題を参考に、
次の条件で“中学1年生向け4択問題”を1問だけ作成してください。

【出題要件】
- 教科: {subject}
- 単元: {topic}
- 難易度: {level}
- 必ず指導要領の範囲内、基礎用語・公式・考え方も確認する
- 本物のテストそっくりに「正しい日本語」「ひっかけ」「実在の選択肢」も含める
- 必ず全て日本語で、中学1年生が理解できる語彙と文体で
- JSON形式で次の全項目を出力（distractor_reasonには、各選択肢ごとの誤答理由やミスしやすいポイントを必ず含める）

【出力形式（例を必ず参考に）】
{{
  "question": "一次方程式x+3=7を解きなさい。",
  "choices": ["x=4", "x=10", "x=3", "x=7"],
  "answer": "x=4",
  "explanation": "xに3を足して7になるから、3を引いてx=4。",
  "correct_message": "よくできました！",
  "incorrect_message": "間違えた選択肢の理由もチェックしよう！",
  "distractor_reason": [
      "正しい", 
      "両辺に足し算をしてしまうミス", 
      "xにそのまま数字を当てはめるミス", 
      "右辺をそのまま答えにするミス"
  ]
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

                # 誤答理由特定
                d_reason = None
                if not correct and "distractor_reason" in qa_data:
                    try:
                        idx = qa_data["choices"].index(user_answer)
                        d_reason = qa_data["distractor_reason"][idx]
                    except Exception:
                        d_reason = None

                save_answer_log(
                    st.session_state.user_id,
                    subject,
                    topic,
                    qa_data["question"],
                    user_answer,
                    int(correct),
                    level=level,
                    distractor_reason=d_reason,
                )

                if correct:
                    st.success(
                        f"正解！ {qa_data.get('correct_message', 'よくできました！')}"
                    )
                else:
                    st.error(
                        f"不正解... {qa_data.get('incorrect_message', 'がんばれ！')}"
                    )
                    if d_reason:
                        st.info(f"ヒント: {d_reason}")
        else:
            # 結果・解説表示
            correct = st.session_state.selected_choice == qa_data["answer"]
            if correct:
                st.success(
                    f"正解！ {qa_data.get('correct_message', 'よくできました！')}"
                )
            else:
                st.error(f"不正解... {qa_data.get('incorrect_message', 'がんばれ！')}")
                # 再度ヒント
                if "distractor_reason" in qa_data:
                    try:
                        idx = qa_data["choices"].index(st.session_state.selected_choice)
                        d_reason = qa_data["distractor_reason"][idx]
                        if d_reason:
                            st.info(f"ヒント: {d_reason}")
                    except Exception:
                        pass
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
