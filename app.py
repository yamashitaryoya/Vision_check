import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random
from datetime import datetime


# -----------------------------
# Google スプレッドシート認証
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Secrets からサービスアカウント情報を取得
# st.secretsは .streamlit/secrets.toml の情報を辞書として読み込みます
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=scope
)

# 認証情報を使ってクライアントを初期化
client = gspread.authorize(creds)

# SecretsからシートIDを取得し、スプレッドシートを開く
sheet_id = st.secrets["sheet_id"]
sheet = client.open_by_key(sheet_id).sheet1

# 視力表の文字
TEST_LETTERS = ["C", "D", "E", "F", "G", "O", "P", "Q"]
VISION_LEVELS = {1.0: 40, 0.7: 60, 0.5: 80, 0.3: 100, 0.1: 150}

if "current_level" not in st.session_state:
    st.session_state.current_level = 1.0
if "history" not in st.session_state:
    st.session_state.history = []

# 名前入力
name = st.text_input("被験者の名前を入力してください")

st.write("画面に表示される文字を読んでください。")

# ランダムに文字を表示
letter = random.choice(TEST_LETTERS)
size = VISION_LEVELS[st.session_state.current_level]
st.markdown(f"<p style='font-size:{size}px; text-align:center;'>{letter}</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Yes（読めた）"):
        st.session_state.history.append((st.session_state.current_level, True))
        levels = list(VISION_LEVELS.keys())
        idx = levels.index(st.session_state.current_level)
        if idx > 0:
            st.session_state.current_level = levels[idx - 1]

with col2:
    if st.button("No（読めない）"):
        st.session_state.history.append((st.session_state.current_level, False))
        levels = list(VISION_LEVELS.keys())
        idx = levels.index(st.session_state.current_level)
        if idx < len(levels) - 1:
            st.session_state.current_level = levels[idx + 1]

# 検査終了
if st.button("検査終了"):
    if not name:
        st.warning("名前を入力してください。")
    elif st.session_state.history:
        readable_levels = [lvl for lvl, result in st.session_state.history if result]
        final_vision = max(readable_levels) if readable_levels else 0.1

        st.success(f"{name} さんの推定視力は **{final_vision}** です")

        # Google Sheets に保存
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name, final_vision, str(st.session_state.history)])

        st.write("結果をGoogle Sheetsに保存しました ✅")

        # リセット
        st.session_state.current_level = 1.0
        st.session_state.history = []
    else:
        st.warning("まだ検査を行っていません。")
