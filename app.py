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




# --- アプリの基本設定 ---
st.set_page_config(page_title="簡易視力検査アプリ", layout="centered")

# 視力レベルとそれに対応する文字サイズ(px)
VISION_LEVELS = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "11": 11,
    "12": 12,
    "13": 13,
    "14": 14,
    "15": 15,
    "16": 16,
    "17": 17,
    "18": 18,
    "19": 19,
}
LEVELS_LIST = list(VISION_LEVELS.keys())

# ランドルト環の向き (CSSの回転角度に対応)
DIRECTIONS = {"右": 0, "下": 90, "左": 180, "上": 270}
DIRECTION_NAMES = list(DIRECTIONS.keys())


# --- Session State の初期化 ---
# アプリケーションの状態を管理するための変数
if "current_level" not in st.session_state:
    st.session_state.current_level = "10"  # 開始時の視力レベル
if "history" not in st.session_state:
    st.session_state.history = []  # 検査履歴を保存
if "correct_direction" not in st.session_state:
    st.session_state.correct_direction = random.choice(DIRECTION_NAMES)
if "test_started" not in st.session_state:
    st.session_state.test_started = False


# --- アプリの表示部分 ---
st.title("簡易視力検査アプリ")
st.markdown("---")

# --- 使い方と注意書き ---
with st.expander("初めての方はこちらをお読みください", expanded=True):
    st.header("使い方")
    st.markdown("""
    1.  名前を入力し、**「検査開始」**ボタンを押してください。
    2.  画面中央に**ランドルト環（輪っかの切れ目）**が表示されます。
    3.  切れ目の方向（上、下、左、右）を**ボタンで回答**してください。
    4.  正解すると、より小さいランドルト環が表示されます（次のレベルへ）。
    5.  不正解の場合、より大きいランドルト環が表示されます（前のレベルへ）。
    6.  測定を終了したい場合は**「検査終了」**ボタンを押してください。
    """)

    st.header("ご注意")
    st.warning("""
    -   スマートフォンからは約40cm離れてください。
    -   画面を明るくし、明るい部屋で検査を行ってください。
    -   片目ずつ、目を細めずに見てください。
    """)

st.markdown("---")

# --- 検査部分 ---
st.header("視力検査")

name = st.text_input("お名前を入力してください", key="user_name")

if st.button("検査開始", disabled=st.session_state.test_started):
    if name:
        st.session_state.test_started = True
        # 検査開始時に状態をリセット
        st.session_state.current_level = "10"
        st.session_state.history = []
        st.rerun()
    else:
        st.warning("お名前を入力してください。")


if st.session_state.test_started:
    # 現在の視力レベルと文字サイズを取得
    level = st.session_state.current_level
    size = VISION_LEVELS[level]
    
    st.info(f"現在の検査レベル: 視力 {level}")

    # ランドルト環を表示 (HTMLとCSSで回転させる)
    rotate_angle = DIRECTIONS[st.session_state.correct_direction]
    st.markdown(
        f"<p style='font-size:{size}px; text-align:center; transform: rotate({rotate_angle}deg);'>C</p>",
        unsafe_allow_html=True,
    )
    
    st.write("ランドルト環の切れ目の方向はどちらですか？")

    # 回答ボタンを4つ横に並べる
    cols = st.columns(4)
    for i, direction in enumerate(DIRECTION_NAMES):
        with cols[i]:
            if st.button(direction, use_container_width=True):
                is_correct = (direction == st.session_state.correct_direction)
                
                # 履歴に追加
                st.session_state.history.append((level, is_correct))
                
                # 正解・不正解に応じてレベルを更新
                idx = LEVELS_LIST.index(level)
                if is_correct:
                    st.success("正解です！")
                    # 次のレベルへ（リストのより若いインデックスへ）
                    if idx > 0:
                        st.session_state.current_level = LEVELS_LIST[idx - 1]
                else:
                    st.error("不正解です。")
                    # 前のレベルへ（リストのより大きいインデックスへ）
                    if idx < len(LEVELS_LIST) - 1:
                        st.session_state.current_level = LEVELS_LIST[idx + 1]

                # 次の問題のために新しい向きをランダムに設定
                st.session_state.correct_direction = random.choice(DIRECTION_NAMES)
                st.rerun() # 画面を再読み込みして新しい問題を表示

# --- 検査終了処理 ---
if st.session_state.test_started:
    if st.button("検査終了", type="primary"):
        if st.session_state.history:
            # 正解したレベルの中から、最も良い視力（数値が大きい）を結果とする
            correct_levels = [float(lvl) for lvl, result in st.session_state.history if result]
            
            if correct_levels:
                final_vision = max(correct_levels)
                st.success(f"## {name} さんの推定視力は **{final_vision}** です")
                st.balloons()
            else:
                final_vision = "0.1未満"
                st.warning(f"## {name} さんの推定視力は **{final_vision}** です")

            # --- Google Sheets に保存 ---
            if st.session_state.get("gsheet_ready", False):
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([timestamp, name, str(final_vision), str(st.session_state.history)])
                    st.write("結果をGoogle Sheetsに保存しました ✅")
                except Exception as e:
                    st.error("結果の保存に失敗しました。")
                    st.error(e)
            
        else:
            st.warning("まだ一度も回答していません。")
            
