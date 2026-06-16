import streamlit as st
from pypdf import PdfReader
from google import genai

# StreamlitのSecretsからAPIキーを取得してGeminiを準備
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("APIキーが見つかりません。Streamlit CloudのSecrets設定を確認してください。")
    st.stop()

st.title("📚 大学生向け学習サポートアプリ")
st.write("講義資料（PDF）をアップロードすると、AIが要約と用語解説を作成します！")

# ファイルアップロード機能
uploaded_file = st.file_uploader("PDFファイルを選択", type="pdf")

if uploaded_file is not None:
    # 1. PDFからテキストを抽出
    reader = PdfReader(uploaded_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    
    # テキストが抽出できた場合のみAIに処理させる
    if extracted_text.strip():
        st.success("📄 資料の読み込みに成功しました！AIが解説を作成中です...")
        
        # 2. Geminiにお願いする指示（プロンプト）を作成
        prompt = f"""
        以下のテキストは大学の講義資料です。これを学習する大学生のために、以下の2点を作成してください。
        語尾は「〜だ」「〜である」調で統一し、無駄な装飾や会話的な表現は避けて簡潔に記述してください。
        
        1. 全体の要約（箇条書きで3〜5つ程度）
        2. 重要な専門用語のピックアップと、そのわかりやすい解説

        【講義資料のテキスト】
        {extracted_text}
        """
        
        try:
            # 3. Geminiにテキストを送信して回答をもらう
            response = client.models.generate_content(
                model='gemini-2.5-flash', # 最新の高速モデル
                contents=prompt,
            )
            
            # 4. 結果を画面に表示
            st.subheader("💡 AIによる要約と解説")
            st.write(response.text)
            
            # おまけ：抽出した生のテキストは折りたたみメニューに入れておく（画面がすっきりします）
            with st.expander("元の抽出テキストを確認する"):
                st.text_area("資料の内容", extracted_text, height=200)
                
        except Exception as e:
            st.error(f"AIの処理中にエラーが発生しました: {e}")
            
    else:
        st.warning("テキストを抽出できませんでした。画像中心のPDFの可能性があります。")
