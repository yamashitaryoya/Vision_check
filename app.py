import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random
from datetime import datetime
import time


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



# --- ロジック設定 ---
TRIALS_PER_LEVEL = 5  # 1レベルあたりの最大試行回数
CORRECT_TO_PASS = 3   # クリアに必要な正解数
FAIL_LIMIT = TRIALS_PER_LEVEL - CORRECT_TO_PASS + 1 # 失敗が確定する不正解数 (この場合は3)

# レベル設定
# レベル名はご意向に沿い「1」～「19」とし、フォントサイズのみを実用的な値に割り当てています。
# レベル1が最も大きく（簡単）、レベル19が最も小さく（困難）になります。
VISION_LEVELS = {
    "1": 19, "2": 18, "3": 17, "4": 16, "5": 15, "6": 14,
    "7": 13, "8": 12, "9": 11, "10": 10, "11": 9, "12": 8,
    "13": 7, "14": 6, "15": 5, "16": 4, "17": 3, "18": 2, "19": 1
}
LEVELS_LIST = list(VISION_LEVELS.keys()) # ["1", "2", ..., "19"]

# ランドルト環の向き
DIRECTIONS = {"右": 0, "下": 90, "左": 180, "上": 270}
DIRECTION_NAMES = list(DIRECTIONS.keys())

# --- Session State の初期化 ---
def init_test_state():
    """検査状態を初期化/リセットする関数"""
    st.session_state.current_level = "10" 
    st.session_state.history = []
    st.session_state.correct_direction = random.choice(DIRECTION_NAMES)
    st.session_state.trial_count = 0
    st.session_state.correct_count = 0
    st.session_state.cleared_levels = []

if "test_started" not in st.session_state:
    st.session_state.test_started = False
    init_test_state()

# --- アプリの表示部分 ---
st.title("総体能力測定")
st.markdown("---")

with st.expander("こちらをお読みください", expanded=True):
    st.header("使い方")
    st.markdown(f"""
    1.  名前を入力し、**「検査開始」**ボタンを押してください。
    2.  各レベルで**最大{TRIALS_PER_LEVEL}問**出題されます。**{CORRECT_TO_PASS}問正解**すると次のレベルに進みます。
    3.  表示されたマークの切れ目の方向をボタンで回答してください。
    4.  測定を終了したい場合は**「検査終了」**ボタンを押してください。
    """)
    st.header("ご注意")
    st.warning("""
    -   画面から少し離れてください。
    -   画面を明るくし、明るい部屋で検査を行ってください。
    -   片目ずつ、目を細めずに見てください。
    """)

st.markdown("---")

# --- 検査部分 ---
st.header("測定")

if not st.session_state.test_started:
    name = st.text_input("お名前を入力してください", key="user_name")
    if st.button("検査開始"):
        if name:
            st.session_state.test_started = True
            st.session_state.user_name_saved = name
            init_test_state()
            st.rerun()
        else:
            st.warning("お名前を入力してください。")
else:
    level = st.session_state.current_level
    size = VISION_LEVELS[level]

    st.info(f"レベル: {level} ({st.session_state.trial_count + 1}問目 / {TRIALS_PER_LEVEL}問中)  |  正解数: {st.session_state.correct_count} / {CORRECT_TO_PASS}")

    rotate_angle = DIRECTIONS[st.session_state.correct_direction]
    st.markdown(
        f"<p style='font-size:{size}px; text-align:center; transform: rotate({rotate_angle}deg);'>C</p>",
        unsafe_allow_html=True,
    )
    
    st.write("マークの切れ目の方向はどちらですか？")

    cols = st.columns(4)
    for i, direction in enumerate(DIRECTION_NAMES):
        with cols[i]:
            if st.button(direction, use_container_width=True, key=f"btn_{direction}"):
                is_correct = (direction == st.session_state.correct_direction)
                st.session_state.history.append((level, is_correct))
                
                st.session_state.trial_count += 1
                if is_correct:
                    st.session_state.correct_count += 1

                level_cleared = (st.session_state.correct_count >= CORRECT_TO_PASS)
                level_failed = ((st.session_state.trial_count - st.session_state.correct_count) >= FAIL_LIMIT)

                if level_cleared:
                    st.toast("レベルクリア！🎉 次のレベルに進みます。")
                    if level not in st.session_state.cleared_levels:
                        st.session_state.cleared_levels.append(level)
                    
                    idx = LEVELS_LIST.index(level)
                    if idx < len(LEVELS_LIST) - 1: # レベルアップ（インデックスを増やす）
                        st.session_state.current_level = LEVELS_LIST[idx + 1]
                    
                    st.session_state.trial_count = 0
                    st.session_state.correct_count = 0

                elif level_failed:
                    st.toast("クリア失敗... 前のレベルに戻ります。")
                    idx = LEVELS_LIST.index(level)
                    if idx > 0: # レベルダウン（インデックスを減らす）
                        st.session_state.current_level = LEVELS_LIST[idx - 1]

                    st.session_state.trial_count = 0
                    st.session_state.correct_count = 0

                st.session_state.correct_direction = random.choice(DIRECTION_NAMES)
                time.sleep(0.5)
                st.rerun()

    # --- 検査終了処理 ---
    if st.button("検査終了", type="primary"):
        if st.session_state.history:
            name_to_display = st.session_state.get("user_name_saved", "被験者")
            # クリアしたレベルの中から最も良いレベル（数値が大きい）を結果とする
            if st.session_state.cleared_levels:
                final_level = max([int(lvl) for lvl in st.session_state.cleared_levels])
                st.success(f"## {name_to_display} さんの達成レベルは **{final_level}** です")
                st.balloons()
            else:
                correct_levels = [int(lvl) for lvl, result in st.session_state.history if result]
                if correct_levels:
                    final_level = max(correct_levels)
                    st.warning(f"## {name_to_display} さんの達成レベルは **{final_level}** です")
                else:
                    final_level = "レベル1未満"
                    st.error(f"## {name_to_display} さんの達成レベルは **{final_level}** です")

            # --- Google Sheets に保存 ---
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_data = [
                    timestamp,
                    name_to_display,
                    str(final_level),
                    str(st.session_state.cleared_levels),
                    str(st.session_state.history)
                ]
                sheet.append_row(row_data)
                st.write("結果をGoogle Sheetsに保存しました ✅")
            except Exception as e:
                st.error("結果の保存に失敗しました。")
                # st.error(e) # デバッグ時にコメント解除
                

            st.session_state.test_started = False
            time.sleep(3)
            st.rerun()
        else:
            st.warning("まだ一度も回答していません。")