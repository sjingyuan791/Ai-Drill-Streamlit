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
        df["created_at"] = pd.to_datetime("today")

    # ---- 1. サマリー（週/⽉/累積タブ） ----
    st.header(f"👑 {username or 'あなた'}の成績アップサマリー")

    tabs = st.tabs(["週", "月", "累積"])
    with tabs[0]:
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

    with tabs[1]:
        month = df["created_at"].dt.to_period("M")
        this_month = month == month.max()
        last_month = month == (month.max() - 1)
        now_cnt = df[this_month].shape[0]
        last_cnt = df[last_month].shape[0]
        now_acc = df[this_month]["is_correct"].mean() if now_cnt > 0 else 0
        last_acc = df[last_month]["is_correct"].mean() if last_cnt > 0 else 0
        st.metric("今月の解答数", now_cnt, now_cnt - last_cnt)
        st.metric("今月の正答率", f"{now_acc*100:.1f}%", f"{(now_acc - last_acc)*100:.1f}%")

    with tabs[2]:
        total_cnt = df.shape[0]
        total_acc = df["is_correct"].mean()
        st.metric("累積の解答数", total_cnt)
        st.metric("累積正答率", f"{total_acc*100:.1f}%")

    # ---- 2. 得意・苦手分析 ----
    st.subheader("🔍 得意・苦手単元分析")
    topic = (
        df.groupby(["subject", "topic"])["is_correct"].agg(["count", "sum", "mean"]).reset_index()
    )
    topic["正答率"] = (100 * topic["mean"]).round(1)
    weak = topic[(topic["count"] >= 3) & (topic["mean"] < 0.8)].sort_values("正答率")
    strong = topic[(topic["count"] >= 3) & (topic["mean"] >= 0.95)].sort_values("正答率", ascending=False)

    # 教科別正答率（レーダー）
    sub = df.groupby("subject")["is_correct"].mean()
    st.plotly_chart(
        {
            "data": [
                {"type": "scatterpolar", "r": [round(100 * x, 1) for x in sub], "theta": list(sub.index), "fill": "toself"}
            ],
            "layout": {"polar": {"radialaxis": {"visible": True, "range": [0, 100]}}, "showlegend": False, "height": 320},
        },
        use_container_width=True,
    )

    st.write("**苦手単元TOP3**（解答3回以上＆正答率80%未満）")
    if len(weak) == 0:
        st.success("苦手単元はありません！")
    else:
        st.dataframe(
            weak[["subject", "topic", "count", "正答率"]].rename(columns={"subject": "教科", "topic": "単元", "count": "解答数"}).head(3)
        )

    st.write("**得意単元TOP3**（正答率95%以上）")
    if len(strong) == 0:
        st.info("得意単元データはまだありません")
    else:
        st.dataframe(
            strong[["subject", "topic", "count", "正答率"]].rename(columns={"subject": "教科", "topic": "単元", "count": "解答数"}).head(3)
        )

    # ---- 3. 学習推移 ----
    st.subheader("📈 学習推移")
    df["date"] = df["created_at"].dt.date
    daily = df.groupby("date")["is_correct"].agg(["count", "mean"])  # 回答数/正答率
    st.bar_chart(daily["count"], use_container_width=True)
    st.line_chart(daily["mean"] * 100, use_container_width=True)

    # ---- 4. 最近の活動履歴 ----
    st.subheader("📝 直近の回答履歴")
    st.dataframe(
        df[["created_at", "subject", "topic", "question", "selected_choice", "is_correct"]]
        .sort_values("created_at", ascending=False)
        .head(10)
    )

    # ---- 5. Next Best Action（次にやるべき3手） ----
    st.subheader("🚀 Next Best Action")
    weakest = weak.iloc[0]["topic"] if len(weak) else "なし"
    left = max(0, 20 - daily["count"].iloc[-7:].sum()) if len(daily) else 20
    # 簡易配分例（弱点優先→他）
    alloc = f"弱点{min(3, left)}問 / 他{max(0, left-3)}問"
    st.markdown(f"""
1. **{weakest}** を中心に3問（誤答傾向を確認）  
2. 週目標20問まで **{left}問**：{alloc}  
3. 速度が落ちる単元は **やさしい** で再入門
""")

    # ---- 6. AIによる今週の学習アドバイス ----
    st.subheader("🤖 AIからの今週のおすすめコメント")
    now_week = df["created_at"].dt.isocalendar().week
    this_week = now_week == now_week.max()
    now_cnt = df[this_week].shape[0]
    now_acc = df[this_week]["is_correct"].mean() if now_cnt > 0 else 0
    summary_txt = f"""
あなたは中学1年生の生徒に寄り添う先生AIです。
この生徒の今週の苦手単元：{','.join(weak['topic']) if len(weak) else 'なし'}
得意単元：{','.join(strong['topic']) if len(strong) else 'なし'}
今週の正答率：{now_acc*100:.1f}％
今週の解答数：{now_cnt}問
直近の誤答傾向を踏まえ、【やる気が出る励まし＋来週の学習のコツ】を200文字以内で日本語で書いてください。
"""
    if st.button("AIアドバイス生成"):
        with st.spinner("AIがコメントを考えています..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": summary_txt}],
                )
                st.info(response.choices[0].message.content)
            except Exception:
                st.warning("AIコメント取得に失敗しました")


# ---- Streamlitページとして呼び出し ----
if __name__ == "__main__":
    dashboard_main()
