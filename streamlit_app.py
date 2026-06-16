import streamlit as st
from pypdf import PdfReader

st.title("📚 大学生向け学習サポートアプリ")
st.write("講義資料（PDF）をアップロードしてください。")

# ファイルアップロード機能
uploaded_file = st.file_uploader("PDFファイルを選択", type="pdf")

if uploaded_file is not None:
    # PDFリーダーを初期化
    reader = PdfReader(uploaded_file)
    
    # 抽出したテキストを保存する変数
    extracted_text = ""
    
    # 全ページをループしてテキストを抽出
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    
    # 抽出結果を画面に表示
    st.subheader("📄 抽出されたテキスト")
    if extracted_text.strip():
        # テキストエリアで表示するとスクロールできて見やすいです
        st.text_area("資料の内容", extracted_text, height=300)
    else:
        st.warning("テキストを抽出できませんでした。画像のみのPDFの可能性があります。")
