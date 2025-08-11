import streamlit as st
import json
from openai import OpenAI
from db import save_answer_log, get_user_answer_stats
from ui_components import show_character_avatar

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# キャラクタープロファイル
character_profiles = {
    "さくら先生": {import streamlit as st
import json
import random
import time
from openai import OpenAI
from db import save_answer_log, get_user_answer_stats
from ui_components import show_character_avatar

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ── キャラクタープロファイル ──────────────────────
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

# ── 中1の単元（学習指導要領準拠） ─────────────────
subjects = {
    "国語": [
        "物語文の読解","説明文・要旨把握","言葉の意味・漢字","品詞・活用","古文・漢文の基礎","俳句・短歌"
    ],
    "数学": [
        "正負の数","文字式","一次方程式","比例・反比例","平面図形","空間図形","資料の整理"
    ],
    "英語": [
        "be動詞・一般動詞","命令文","疑問詞","助動詞can","現在進行形","代名詞","三単現s"
    ],
    "理科": [
        "植物の分類","動物の分類","身のまわりの物質","光と音","大地の変化","大気と水"
    ],
    "社会": [
        "世界のすがた","日本の国土","古代の日本","中世の日本","現代社会の基礎"
    ],
}

# ── 難易度スペック（AIへ明示） ───────────────────
DIFF_SPEC = {
    "やさしい": "用語は教科書レベル。ひっかけ最小。1手順で解ける計算/基本語彙。",
    "ふつう": "教科書+定期試験相当。典型的なひっかけ1つ。2手順程度の推論。",
    "ちょっとむずかしい": "入試基礎レベル。迷わせる選択肢2つ。2〜3手順の多段推論。",
}

# ── 弱点検出（80%未満・3問以上） ─────────────────
def calc_topic_weakness(user_id, subject):
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
    result = sorted([r for r in result if r[1] < 0.8], key=lambda x: x[1])
    weak_topics = [r[0] for r in result]
    return weak_topics

# ── JSON検証（厳格） ─────────────────────────────
def try_parse_and_validate(content: str):
    try:
        s = content[content.find("{"): content.rfind("}") + 1]
        data = json.loads(s)
    except Exception:
        return None
    required = ["question", "choices", "answer", "explanation", "distractor_reason"]
    if any(k not in data for k in required):
        return None
    if not (isinstance(data["choices"], list) and len(data["choices"]) == 4):
        return None
    if not (isinstance(data["distractor_reason"], list) and len(data["distractor_reason"]) == 4):
        return None
    if not isinstance(data["explanation"], str) or len(data["explanation"]) < 80:
        return None
    if data["answer"] not in data["choices"]:
        return None
    return data

# ── フォールバック（LLM失敗時の保険） ───────────────
def fallback_local_item(subject, topic, level):
    # 最低限のダミー（本番ではCSV/DBから供給）
    q = {
        "question": f"【{subject}/{topic}】基本の確認問題：次の中から正しいものを1つ選びなさい。",
        "choices": ["A", "B", "C", "D"],
        "answer": "A",
        "explanation": "この設問はフォールバック問題です。学習範囲の基本事項を確認するため、Aが正解となるように構成されています。",
        "correct_message": "よくできました！",
        "incorrect_message": "基本をもう一度確認しよう！",
        "distractor_reason": [
            "正しい選択肢です。",
            "用語の読み違いによる誤答。",
            "定義の混同による誤答。",
            "数値・根拠の取り違え。",
        ],
    }
    return q

# ── 出題（生成→検証→再試行→フォールバック） ──────────
def generate_question(subject, topic, level, seed):
    prompt = f"""
あなたは日本の中学校教員です。以下の厳密形式で“中学1年生向け4択問題”を **1問だけ** 出力してください。
# 出題条件
- 教科: {subject}
- 単元: {topic}
- 難易度: {level}（要件: {DIFF_SPEC.get(level, '')}）
# 厳格出力要件
- 出力は **JSONのみ**（前後の説明文は一切禁止）。
- choicesは **必ず4つ**。
- distractor_reasonはchoicesと同順で **必ず4つ**。
- explanationは **80文字以上**、根拠・手順・典型ミスを簡潔に記述。
- 文体は中学1年生が読めるやさしい日本語。
- 検定教科書・定期テスト・全国公立高入試の頻出論点を参照。
- seed={seed} を考慮してバリエーションを出すこと。

{{
  "question": "...",
  "choices": ["...","...","...","..."],
  "answer": "...",
  "explanation": "...",
  "correct_message": "よくできました！",
  "incorrect_message": "間違え方のクセを直そう！",
  "distractor_reason": ["...","...","...","..."]
}}
"""
    for _ in range(2):  # 最大2回再試行
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = resp.choices[0].message.content
        data = try_parse_and_validate(content)
        if data:
            return data, "gpt-4o-mini"
    return fallback_local_item(subject, topic, level), "fallback-local"

# ── 適応難易度（簡易ステアケース） ────────────────
def adapt_level(level, recent_results):
    order = ["やさしい", "ふつう", "ちょっとむずかしい"]
    i = order.index(level)
    if len(recent_results) >= 2 and recent_results[-1] and recent_results[-2]:
        i = min(i + 1, 2)  # 連続正解で昇段
    elif recent_results and not recent_results[-1]:
        i = max(i - 1, 0)  # 直近不正解で降段
    return order[i]

# ── 画面本体 ────────────────────────────────────
def drill_main():
    # セッション初期化
    for key, val in {
        "qa_data": None,
        "explanation_loop": 0,
        "show_explanation": False,
        "selected_choice": None,
        "answered": False,
        "started_at": None,
        "seed": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

    st.markdown("### AIドリルで勉強しよう！")
    display_name = st.session_state.get("username") or f"ユーザーID: {st.session_state.user_id}"
    st.write(f"こんにちは、{display_name} さん！")

    character = st.selectbox("AI先生を選んでね", list(character_profiles.keys()))
    show_character_avatar(character, character_profiles)
    subject = st.selectbox("教科をえらぼう！", list(subjects.keys()))

    # 弱点推奨 & 弱点ラリー
    weak_topics = calc_topic_weakness(st.session_state.user_id, subject)
    st.caption("AIがおすすめする順（※正答率80%未満は優先表示）")
    weak_only = st.checkbox("弱点ラリー（苦手単元だけ連続出題）", value=False)
    if weak_only and weak_topics:
        all_topics = weak_topics
    else:
        all_topics = weak_topics + [t for t in subjects[subject] if t not in weak_topics]
    topic = st.selectbox("単元（AIおすすめ順）", all_topics)
    if weak_topics and not weak_only:
        st.info(f"おすすめ: {'・'.join(weak_topics)}（正答率80％未満）")

    # 難易度（適応制御）
    level = st.radio("むずかしさは？", ["やさしい", "ふつう", "ちょっとむずかしい"], index=1)
    level = adapt_level(level, st.session_state.get("recent_corrects", []))
    st.caption(f"適応後の難易度: **{level}**")

    # 出題ボタン
    if st.button("新しい問題を出す", key="generate_q"):
        st.session_state.qa_data = None
        st.session_state.answered = False
        st.session_state.selected_choice = None
        st.session_state.show_explanation = False
        st.session_state.started_at = time.time()
        st.session_state.seed = random.randint(1, 10_000_000)
        with st.spinner("AIが問題を考えています..."):
            try:
                data, ai_version = generate_question(subject, topic, level, st.session_state.seed)
                st.session_state.qa_data = data
                st.session_state.ai_version = ai_version
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
                0 if st.session_state.selected_choice is None else choices.index(st.session_state.selected_choice)
            ),
            disabled=st.session_state.answered,
        )

        if not st.session_state.answered:
            if st.button("答え合わせ", key="answer_btn"):
                st.session_state.answered = True
                user_answer = st.session_state.selected_choice
                correct = user_answer == qa_data["answer"]
                st.session_state.show_explanation = True

                # 誤答理由（選択肢に対応）
                d_reason = None
                if not correct and "distractor_reason" in qa_data:
                    try:
                        idx = qa_data["choices"].index(user_answer)
                        d_reason = qa_data["distractor_reason"][idx]
                    except Exception:
                        d_reason = None

                # 応答時間
                elapsed_ms = int((time.time() - (st.session_state.started_at or time.time())) * 1000)

                # 保存（後方互換）
                try:
                    save_answer_log(
                        st.session_state.user_id,
                        subject,
                        topic,
                        qa_data["question"],
                        user_answer,
                        int(correct),
                        level=level,
                        distractor_reason=d_reason,
                        response_time_ms=elapsed_ms,
                        choice_index=choices.index(user_answer),
                        ai_version=st.session_state.get("ai_version", ""),
                        seed=st.session_state.get("seed"),
                    )
                except TypeError:
                    # 既存シグネチャ用フォールバック
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

                # 表示
                if correct:
                    st.success(qa_data.get("correct_message", "よくできました！"))
                else:
                    st.error(qa_data.get("incorrect_message", "がんばれ！"))
                    if d_reason:
                        st.info(f"ヒント: {d_reason}")

                # 適応難易度のための履歴更新
                recent = st.session_state.get("recent_corrects", [])
                recent.append(bool(correct))
                st.session_state.recent_corrects = recent[-10:]
        else:
            # 結果・解説表示
            correct = st.session_state.selected_choice == qa_data["answer"]
            if correct:
                st.success(qa_data.get("correct_message", "よくできました！"))
            else:
                st.error(qa_data.get("incorrect_message", "がんばれ！"))
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

        # 次の問題へ（自動/手動）
        if st.session_state.answered:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("次の問題へ", key="next_q"):
                    st.session_state.qa_data = None
                    st.session_state.answered = False
                    st.session_state.selected_choice = None
                    st.session_state.show_explanation = False
                    st.rerun()
            with col2:
                st.toggle("このセッションは連続出題", key="auto_next")

            if st.session_state.get("auto_next"):
                time.sleep(2.0)  # 体感テンポを維持
                st.session_state.qa_data = None
                st.session_state.answered = False
                st.session_state.selected_choice = None
                st.session_state.show_explanation = False
                st.rerun()
    else:
        st.info("「新しい問題を出す」ボタンを押してスタート！")
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

