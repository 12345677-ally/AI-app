import streamlit as st
from pypdf import PdfReader
from google import genai

# APIキーの設定
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("APIキーが見つかりません。")
    st.stop()

# --- AIの回答を記憶（キャッシュ）する関数 ---
@st.cache_data
def generate_summary(text):
    prompt = f"""
    以下のテキストは大学の講義資料です。これを学習する大学生のために、以下の2点を作成してください。
    語尾は「〜だ」「〜である」調で統一し、無駄な装飾や会話的な表現は避けて簡潔に記述してください。

    1. 全体の要約
    2. 重要な専門用語のピックアップと、その簡潔な解説

    【講義資料のテキスト】
    {text}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

@st.cache_data
def generate_test(text):
    prompt = f"""
    以下の講義資料を基に、学習者の理解度を測る重要な確認問題を3問作成してください。
    語尾は「〜だ」「〜である」調で統一し、簡潔に記述してください。
    必ず以下の「---」で区切られたフォーマット通りに出力してください。

    【問題】
    1. (問題文)
    2. (問題文)
    3. (問題文)
    ---
    【解答と解説】
    1. (解答) - (簡潔な解説)
    2. (解答) - (簡潔な解説)
    3. (解答) - (簡潔な解説)

    【講義資料のテキスト】
    {text}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text
# ---------------------------------------------

st.title("📚 大学生向け学習サポートアプリ")
st.write("講義資料（PDF）をアップロードすると、AIが要約とテストを作成します。")

uploaded_file = st.file_uploader("PDFファイルを選択", type="pdf")

if uploaded_file is not None:
    # PDFからテキストを抽出
    reader = PdfReader(uploaded_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    
    if extracted_text.strip():
        st.success("📄 資料の読み込みに成功しました！")
        
        # 1. 要約の表示（自動生成）
        st.subheader("💡 AIによる要約と解説")
        with st.spinner("要約を作成中..."):
            summary = generate_summary(extracted_text)
            st.write(summary)
            
        st.divider() # 区切り線

        # 2. テキスト生成機能（ボタンで起動）
        st.subheader("📝 理解度チェックテスト")
        st.write("資料の要点が掴めたら、テストで定着度を確認しよう。")
        
        if st.button("この資料からテストを作成する"):
            with st.spinner("テストを作成中..."):
                test_output = generate_test(extracted_text)
                
                # 「---」で問題と解答を分割して表示
                if "---" in test_output:
                    questions, answers = test_output.split("---", 1)
                    st.write(questions.strip())
                    
                    # 解答は折りたたみメニューに隠す
                    with st.expander("解答と解説を見る"):
                        st.write(answers.strip())
                else:
                    st.write(test_output)
                    st.warning("想定外のフォーマットで出力されました。")
                    
        with st.expander("元の抽出テキストを確認する"):
            st.text_area("資料の内容", extracted_text, height=200)
            
    else:
        st.warning("テキストを抽出できませんでした。")
