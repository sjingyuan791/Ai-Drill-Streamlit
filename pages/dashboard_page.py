import streamlit as st
import pandas as pd
from db import get_user_answer_stats
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def dashboard_main():
    st.title("📊 学習ダッシュボード")
    user_id = st.session_state.user_id
    username = st.session_state.get("username", "")

    # 解答データ取得
    data = get_user_answer_stats(user_id)
    if not data or len(data) == 0:
        st.info("まだ学習履歴がありません。AIドリルで演習しましょう！")
        return

    df = pd.DataFrame(data)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
    else:
        df["created_at"] = pd.to_datetime("today")  # 仮

    # ---- 1. サマリー ----
    st.header(f"👑 {username or 'あなた'}の成績アップサマリー")
    week = df["created_at"].dt.isocalendar().week
    this_week = week == week.max()
    last_week = week == (week.max() - 1)
    now_cnt = df[this_week].shape[0]
    last_cnt = df[last_week].shape[0]
    now_acc = df[this_week]["is_correct"].mean() if now_cnt > 0 else 0
    last_acc = df[last_week]["is_correct"].mean() if last_cnt > 0 else 0
    st.metric("今週の解答数", now_cnt, now_cnt - last_cnt)
    st.metric("今週の正答率", f"{now_acc*100:.1f}%", f"{(now_acc - last_acc)*100:.1f}%")
    st.metric("連続学習日数", (df["created_at"].dt.date.nunique()))
    st.progress(min(now_cnt / 20, 1.0), text="今週の目標：20問")

    # ---- 2. 得意・苦手分析 ----
    st.subheader("🔍 得意・苦手単元分析")
    topic = (
        df.groupby(["subject", "topic"])["is_correct"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )
    topic["正答率"] = (100 * topic["mean"]).round(1)
    weak = topic[(topic["count"] >= 3) & (topic["mean"] < 0.8)].sort_values("正答率")
    strong = topic[(topic["count"] >= 3) & (topic["mean"] >= 0.95)].sort_values(
        "正答率", ascending=False
    )

    # レーダーチャート用（教科別正答率）
    sub = df.groupby("subject")["is_correct"].mean()
    st.plotly_chart(
        {
            "data": [
                {
                    "type": "scatterpolar",
                    "r": [round(100 * x, 1) for x in sub],
                    "theta": list(sub.index),
                    "fill": "toself",
                }
            ],
            "layout": {
                "polar": {"radialaxis": {"visible": True, "range": [0, 100]}},
                "showlegend": False,
                "height": 320,
            },
        },
        use_container_width=True,
    )

    st.write("**苦手単元TOP3**（解答3回以上＆正答率80%未満）")
    if len(weak) == 0:
        st.success("苦手単元はありません！")
    else:
        st.dataframe(
            weak[["subject", "topic", "count", "正答率"]]
            .rename(columns={"subject": "教科", "topic": "単元", "count": "解答数"})
            .head(3)
        )

    st.write("**得意単元TOP3**（正答率95%以上）")
    if len(strong) == 0:
        st.info("得意単元データはまだありません")
    else:
        st.dataframe(
            strong[["subject", "topic", "count", "正答率"]]
            .rename(columns={"subject": "教科", "topic": "単元", "count": "解答数"})
            .head(3)
        )

    # ---- 3. 学習推移グラフ ----
    st.subheader("📈 学習推移")
    df["date"] = df["created_at"].dt.date
    daily = df.groupby("date")["is_correct"].agg(["count", "mean"])
    st.bar_chart(daily["count"], use_container_width=True)
    st.line_chart(daily["mean"] * 100, use_container_width=True)

    # ---- 4. 最近の活動履歴 ----
    st.subheader("📝 直近の回答履歴")
    st.dataframe(
        df[
            [
                "created_at",
                "subject",
                "topic",
                "question",
                "selected_choice",
                "is_correct",
            ]
        ]
        .sort_values("created_at", ascending=False)
        .head(10)
    )

    # ---- 5. AIによる今週の学習アドバイス ----
    st.subheader("🤖 AIからの今週のおすすめコメント")
    summary_txt = f"""
あなたは中学1年生の生徒に寄り添う先生AIです。
この生徒の今週の苦手単元：{','.join(weak['topic']) if len(weak) else "なし"}
得意単元：{','.join(strong['topic']) if len(strong) else "なし"}
今週の正答率：{now_acc*100:.1f}％
今週の解答数：{now_cnt}問
直近で連続間違えが多い単元や、全体の傾向から【中学生にやる気が出る励まし＋来週の学習のコツ】を200文字以内で書いてください。
"""
    if st.button("AIアドバイス生成"):
        with st.spinner("AIがコメントを考えています..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": summary_txt}],
                )
                st.info(response.choices[0].message.content)
            except Exception as e:
                st.warning("AIコメント取得に失敗しました")


# ---- Streamlitページとして呼び出し ----
if __name__ == "__main__":
    dashboard_main()
