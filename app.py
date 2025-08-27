import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# Google スプレッドシート認証
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Secrets からサービスアカウント情報を取得
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_id"]).sheet1

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("簡易視力検査シミュレーション")

# 名前入力
name = st.text_input("名前を入力してください")

# 視力選択
st.subheader("視力を選択してください")
vision_options = ["1.5", "1.2", "1.0", "0.8", "0.6", "0.4", "0.2", "0.1"]
vision = st.selectbox("視力", vision_options)

# 保存ボタン
if st.button("結果を保存"):
    if not name:
        st.error("名前を入力してください")
    else:
        # Google スプレッドシートに追加
        sheet.append_row([name, vision])
        st.success(f"{name}さんの視力 {vision} を保存しました")

# -----------------------------
# 過去データ表示（任意）
# -----------------------------
if st.checkbox("過去の結果を表示"):
    data = sheet.get_all_records()
    if data:
        st.table(data)
    else:
        st.info("まだ記録はありません")
