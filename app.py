import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random
from datetime import datetime
import time

# -----------------------------
# Google スプレッドシート認証（キャッシュ機能を追加）
# -----------------------------
@st.cache_resource
def get_spreadsheet():
    """
    Googleスプレッドシートに接続し、シートオブジェクトを返す。
    @st.cache_resourceデコレータにより、この関数の結果はキャッシュされ、
    アプリの再実行時に関数が再呼び出しされるのを防ぎます。
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )
    client = gspread.authorize(creds)
    sheet_id = st.secrets["sheet_id"]
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

# キャッシュされた関数を呼び出して、シートオブジェクトを取得
sheet = get_spreadsheet()


# --- ロジック設定 ---
CORRECT_TO_PASS = 3   # クリアに必要な正解数
MISTAKE_LIMIT = 2     # 失敗となる不正解数

# レベル設定
VISION_LEVELS = {
    "1": 19, "2": 18, "3": 17, "4": 16, "5": 15, "6": 14,
    "7": 13, "8": 12, "9": 11, "10": 10, "11": 9, "12": 8,
    "13": 7, "14": 6, "15": 5, "16": 4, "17": 3, "18": 2, "19": 1
}
LEVELS_LIST = list(VISION_LEVELS.keys())

# ランドルト環の向き
DIRECTIONS = {"右": 0, "下": 90, "左": 180, "上": 270}
DIRECTION_NAMES = list(DIRECTIONS.keys())


# --- 測定終了処理を関数化 ---
def end_test():
    """測定終了 → 結果を保存"""
    name = st.session_state.get("user_name_saved", "被験者")
    if st.session_state.cleared_levels:
        final_level = max([int(lvl) for lvl in st.session_state.cleared_levels])
        st.success(f"## {name} さんの達成レベルは **{final_level}** です")
        st.balloons()
    else:
        final_level = "レベル1未満"
        st.error(f"## {name} さんの達成レベルは **{final_level}** です")

    # --- Google Sheets に保存 ---
    try:
        # 保存するデータを氏名と最終レベルのみに変更
        row_data = [name, str(final_level)]
        sheet.append_row(row_data)
        st.write("結果をGoogle Sheetsに保存しました ✅")
    except Exception as e:
        # エラーが発生した場合、内容を表示するように変更
        st.error(f"結果の保存に失敗しました: {e}")

    # 状態をリセット
    st.session_state.test_started = False
    time.sleep(4)
    st.rerun()

# --- Session State の初期化 ---
def init_test_state():
    """測定状態を初期化/リセットする関数"""
    st.session_state.current_level = "10"
    st.session_state.history = []
    st.session_state.correct_direction = random.choice(DIRECTION_NAMES)
    st.session_state.trial_count = 0
    st.session_state.correct_count = 0
    st.session_state.cleared_levels = []
    st.session_state.ended_by_failure = False

if "test_started" not in st.session_state:
    st.session_state.test_started = False
    init_test_state()
# --- アプリの表示部分 ---
st.title("しりょくけんさ")
st.markdown("---")

with st.expander("必ずこちらをお読みください", expanded=True):
    st.subheader("使い方")
    st.markdown(f"""
    1.  氏名を入力し、「検査開始」ボタンを押してください。
    2.  各レベルで**{CORRECT_TO_PASS}問正解**すると次のレベルに進みます。
    3.  **{MISTAKE_LIMIT}問間違える**と、測定は**終了**となります。
    4.  途中でやめる場合は「測定終了」ボタンを押してください。
    """)
    st.subheader("ご注意")
    st.warning("""
    -   webサイトの拡大・縮小機能は使用しないでください。
    -   **腕を完全に伸ばした状態**（目安：60cm）で、検査を行ってください。
    -   普段、眼鏡やコンタクトレンズを使用している場合は、必ず装着した状態で検査を行ってください。
    -   **画面の明るさを100% に設定**し、**ダークモードの場合はオフに設定**し、明るい部屋で検査を行ってください。
    -   **分からないものは必ず「わからない」ボタンを押してください。**
    """)

st.markdown("---")

# --- 測定部分 ---
if not st.session_state.test_started:
    st.header("測定開始")
    name = st.text_input("氏名を入力してください", key="user_name")
    if st.button("測定開始"):
        if name:
            st.session_state.test_started = True
            st.session_state.user_name_saved = name
            init_test_state()
            st.rerun()
        else:
            st.warning("氏名を入力してください。")
else:
    st.header("測定中")
    level = st.session_state.current_level
    size = VISION_LEVELS[level]
    incorrect_count = st.session_state.trial_count - st.session_state.correct_count

    st.info(f"レベル: {level} ({st.session_state.trial_count + 1}問目)  |  正解: {st.session_state.correct_count}  |  不正解: {incorrect_count}")

    rotate_angle = DIRECTIONS[st.session_state.correct_direction]
    st.markdown(
        f"<p style='font-size:{size}px; text-align:center; transform: rotate({rotate_angle}deg);'>C</p>",
        unsafe_allow_html=True,
    )
    
    st.write("切れ目の方向はどちらですか？")
    
    button_labels = DIRECTION_NAMES + ["わからない"]
    cols = st.columns(len(button_labels))
    
    for i, label in enumerate(button_labels):
        with cols[i]:
            if st.button(label, use_container_width=True, key=f"btn_{label}"):
                
                if label == "わからない":
                    is_correct = False
                else:
                    is_correct = (label == st.session_state.correct_direction)
                
                st.session_state.history.append((level, is_correct))
                
                st.session_state.trial_count += 1
                if is_correct:
                    st.session_state.correct_count += 1

                current_incorrect_count = st.session_state.trial_count - st.session_state.correct_count

                level_cleared = (st.session_state.correct_count >= CORRECT_TO_PASS)
                level_failed = (current_incorrect_count >= MISTAKE_LIMIT)

                if level_failed:
                    st.session_state.ended_by_failure = True
                    end_test()
                
                else:
                    if level_cleared:
                        st.toast("レベルクリア！🎉 次のレベルに進みます。")
                        if level not in st.session_state.cleared_levels:
                            st.session_state.cleared_levels.append(level)
                        
                        idx = LEVELS_LIST.index(level)
                        if idx < len(LEVELS_LIST) - 1:
                            st.session_state.current_level = LEVELS_LIST[idx + 1]
                        
                        st.session_state.trial_count = 0
                        st.session_state.correct_count = 0
                        time.sleep(0.5)

                    previous_direction = st.session_state.correct_direction
                    possible_directions = [d for d in DIRECTION_NAMES if d != previous_direction]
                    st.session_state.correct_direction = random.choice(possible_directions)
                    
                    st.rerun()

    if st.button("測定終了", type="primary"):
        end_test()