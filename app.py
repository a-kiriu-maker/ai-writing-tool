"""AIライティングツール（Streamlit + Gemini API）"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from gemini_client import stream_text
from tools import TOOLS

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")

if "results" not in st.session_state:
    st.session_state.results = {}  # ツールごとの最新の結果
if "history" not in st.session_state:
    st.session_state.history = []  # 全ツールの生成履歴

# ---------------------------------------------------------------- サイドバー
with st.sidebar:
    st.title("✍️ AIライティング")
    tool = st.radio(
        "ツール",
        TOOLS,
        format_func=lambda t: f"{t.icon} {t.label}",
        label_visibility="collapsed",
    )

    st.divider()
    with st.expander("⚙️ 設定", expanded=not os.getenv("GEMINI_API_KEY")):
        api_key = st.text_input(
            "Gemini APIキー",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            help=".env に GEMINI_API_KEY を書いておくと毎回入力せずに済みます。",
        )
        model = st.text_input("モデル", value=DEFAULT_MODEL)

    if st.session_state.history:
        st.divider()
        st.caption("生成履歴")
        for item in reversed(st.session_state.history):
            with st.expander(f"{item['time']} {item['tool']}"):
                st.markdown(item["text"])

# ---------------------------------------------------------------- メイン
st.header(f"{tool.icon} {tool.label}")
st.caption(tool.description)

request = tool.render()

if request:
    if not api_key:
        st.error("サイドバーの「設定」で Gemini APIキーを入力してください。")
        st.stop()
    st.subheader("生成結果")
    try:
        with st.spinner("読み込み・生成中..." if request.files else "生成中..."):
            text = st.write_stream(
                stream_text(
                    api_key, model, request.system, request.prompt, request.temperature, request.files
                )
            )
    except Exception as e:  # APIキー間違い・モデル名違い・通信エラーなどをまとめて表示
        if "503" in str(e) or "429" in str(e):
            st.warning(
                "Gemini（Google側）が混み合っているため、予備のモデルも含めて何度か試しましたが生成できませんでした。"
                "1〜2分ほど待ってから、もう一度ボタンを押してください。"
            )
        else:
            st.error(f"生成に失敗しました: {e}")
        st.stop()
    st.session_state.results[tool.key] = text
    st.session_state.history.append(
        {"time": datetime.now().strftime("%H:%M"), "tool": tool.label, "text": text}
    )
    st.rerun()  # 結果を下の表示ブロックで描き直し、履歴にも反映する

if result := st.session_state.results.get(tool.key):
    st.subheader("生成結果")
    tab_view, tab_copy = st.tabs(["プレビュー", "コピー用テキスト"])
    with tab_view:
        st.markdown(result)
    with tab_copy:
        st.code(result, language=None, wrap_lines=True)
    col1, col2 = st.columns(2)
    col1.download_button(
        "📥 テキストで保存",
        result,
        file_name=f"{tool.key}_{datetime.now():%Y%m%d_%H%M}.md",
        mime="text/markdown",
        width="stretch",
    )
    if col2.button("🗑️ 結果をクリア", width="stretch"):
        del st.session_state.results[tool.key]
        st.rerun()
