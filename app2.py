import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="RTS Powerlifting Pro", layout="wide")
DATA_FILE = "training_log.csv"

# --- データ保存・読み込み・削除関数 ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Date", "Exercise", "Weight", "RPE", "E1RM", "Memo"])
    return pd.read_csv(DATA_FILE)

def save_data(date, exercise, weight, rpe, e1rm, memo):
    df = load_data()
    new_data = pd.DataFrame({
        "Date": [date], "Exercise": [exercise], "Weight": [weight],
        "RPE": [rpe], "E1RM": [e1rm], "Memo": [memo]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# 【追加】指定した行（インデックス）を削除する関数
def delete_data_row(index):
    df = load_data()
    if index in df.index:
        df = df.drop(index) # 指定行を削除
        df.to_csv(DATA_FILE, index=False) # 保存し直す

# --- サイドバー設定 ---
st.sidebar.title("⚙️ 設定")
week = st.sidebar.slider("現在の週 (Week)", 1, 12, 1)

st.sidebar.markdown("---")
st.sidebar.subheader("目標/MAX設定")

sq_max = st.sidebar.number_input("SQ MAX (kg)", value=200.0, step=2.5)
bp_max = st.sidebar.number_input("BP MAX (kg)", value=115.0, step=2.5)
dl_max = st.sidebar.number_input("DL MAX (kg)", value=210.0, step=2.5)

# プレート計算機（サイドバー）
st.sidebar.markdown("---")
with st.sidebar.expander("🧮 プレート計算機"):
    req_weight = st.number_input("使いたい重量 (kg)", value=100.0, step=2.5)
    bar_weight = 20.0
    if req_weight >= bar_weight:
        one_side = (req_weight - bar_weight) / 2
        st.write(f"片側: **{one_side} kg**")
        plates = [25, 20, 15, 10, 5, 2.5, 1.25]
        text_out = []
        for p in plates:
            count = int(one_side // p)
            if count > 0:
                text_out.append(f"**{p}**kg x {count}")
                one_side -= count * p
        st.write(" | ".join(text_out))

# --- ロジック: RTSフェーズ管理 ---
if week <= 4:
    phase = "Volume Block (基礎作り)"
    desc = "筋量を増やす時期。強度は抑えめ(E1RMの70-75%)で量をこなします。"
    target_intensity = 0.72 
    backoff_info = "6 reps × 4-5 sets"
elif week <= 8:
    phase = "Strength Block (筋力強化)"
    desc = "高重量に慣れる時期。強度は高め(E1RMの80-85%)へ移行します。"
    target_intensity = 0.82 
    backoff_info = "3-4 reps × 3-4 sets"
else:
    phase = "Peaking Block (調整)"
    desc = "試合形式。強度は最大(E1RMの90%以上)、量は最小限にします。"
    target_intensity = 0.90 
    backoff_info = "2 reps × 2-3 sets"

if week == 12:
    phase = "Competition Week (本番)"
    desc = "記録測定日です。"
    target_intensity = 0.0

# --- メイン画面 ---
st.title("🏋️ RTS Powerlifting Pro")
st.info(f"📅 **Week {week}: {phase}**\n\n{desc}")

# --- 1. 当日調整 (Daily Autoregulation) ---
st.markdown("### 1. 本日のトップシングル記録 & 計算")
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    date_input = st.date_input("日付", datetime.today())
    lift_type = st.selectbox("種目", ["Squat", "Bench Press", "Deadlift"])
    
    base_w = sq_max if lift_type == "Squat" else (bp_max if lift_type == "Bench Press" else dl_max)
    top_weight = st.number_input("Top Single重量 (kg)", value=float(int(base_w * 0.9)), step=2.5)
    top_rpe = st.slider("RPE (感覚: 10=限界, 8=あと2回)", 6.0, 10.0, 8.0, 0.5)
    memo = st.text_input("メモ", "調子よし")

# 計算ロジック
rpe_chart = {10:1.0, 9.5:0.96, 9.0:0.92, 8.5:0.89, 8.0:0.86, 7.5:0.84, 7.0:0.81, 6.5:0.79}
coeff = rpe_chart.get(top_rpe, 0.86) 
e1rm = int(top_weight / coeff)
work_weight = int(e1rm * target_intensity)

with col2:
    st.markdown("#### 📊 AI分析結果")
    c1, c2, c3 = st.columns(3)
    c1.metric("今日の推定MAX (E1RM)", f"{e1rm} kg")
    c2.metric("推奨セット重量", f"{work_weight} kg", f"強度 {int(target_intensity*100)}%")
    c3.metric("目標セット数", backoff_info)
    
    if week != 12:
        st.success(f"**指示:** Topシングル **{top_weight}kg** 後、**{work_weight}kg** で **{backoff_info}** を実施")
    else:
        st.warning("今週はMAX測定です！")

    if st.button("💾 データを記録する", type="primary", use_container_width=True):
        save_data(date_input, lift_type, top_weight, top_rpe, e1rm, memo)
        st.toast("保存しました！", icon="✅")

st.divider()

# --- 2. 週間メニュー ---
st.markdown("### 2. 今週の推奨プログラム")
col_d1, col_d2 = st.columns(2)

with col_d1:
    st.info(f"### 🔥 Day 1: Squat Day")
    st.markdown(f"""
    - **Comp Squat (メイン)**: Top {top_weight}kg → **Back off {work_weight}kg**
    - **Bench (Vol)**: {int(bp_max*0.7)}kg × 5-8reps × 4s
    - **Bulgarian SQ**: 10reps × 3s / **Ab Roller**: 10reps × 3s
    """)
    st.success(f"### 💥 Day 3: Bench Press Day")
    st.markdown(f"""
    - **Comp Bench (メイン)**: Top {top_weight}kg → **Back off {work_weight}kg**
    - **Pause Squat**: {int(sq_max*0.65)}kg × 4reps × 3s
    - **Dips**: 10reps × 3s / **Face Pull**: 15reps × 4s
    """)

with col_d2:
    st.warning(f"### 🚀 Day 2: Deadlift Day")
    st.markdown(f"""
    - **Comp Deadlift (メイン)**: Top {top_weight}kg → **Back off {work_weight}kg**
    - **Close Grip BP**: {int(bp_max*0.75)}kg × 6reps × 3s
    - **T-Bar Row**: 10reps × 4s / **Plank**: 60sec × 3s
    """)
    st.error(f"### 🛠️ Day 4: Accessory Day")
    st.markdown(f"""
    - **Spoto Press**: {int(bp_max*0.7)}kg × 6reps × 4s
    - **RDL**: {int(dl_max*0.6)}kg × 8reps × 3s
    - **Pull-up**: 限界まで × 3s / **Arms**: 15reps × 3s
    """)

st.divider()

# --- 3. 履歴グラフ・削除機能 ---
st.markdown("### 3. 成長記録 (E1RM)")
df_hist = load_data()

if not df_hist.empty:
    st.line_chart(df_hist, x="Date", y="E1RM", color="Exercise")
    
    # 【追加機能】詳細データの閲覧と削除
    with st.expander("📝 詳細データ管理・削除"):
        # 最新順に並べ替え
        df_display = df_hist.sort_index(ascending=False)
        st.dataframe(df_display, use_container_width=True)
        
        st.markdown("---")
        st.warning("🗑️ **データの削除**")
        
        # 削除用の選択ボックス（日付と種目を表示）
        delete_target_index = st.selectbox(
            "削除したい記録を選んでください",
            options=df_display.index,
            format_func=lambda x: f"{df_display.loc[x, 'Date']} - {df_display.loc[x, 'Exercise']} ({df_display.loc[x, 'Weight']}kg)"
        )
        
        # 削除ボタン
        if st.button("選択したデータを削除する", type="secondary"):
            delete_data_row(delete_target_index)
            st.rerun() # 画面をリロードして反映
else:
    st.caption("※データはまだありません。")