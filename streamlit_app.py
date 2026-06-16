import streamlit as st
from pypdf import PdfReader
from google import genai

# APIキーの設定
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("APIキーが見つかりません。")
    st.stop()

# --- セッション状態（記憶）の初期化 ---
if "questions" not in st.session_state:
    st.session_state.questions = None
if "grading_result" not in st.session_state:
    st.session_state.grading_result = None
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# --- AIの関数（キャッシュ対応） ---
@st.cache_data
def generate_summary(text):
    prompt = f"""
    以下のテキストは大学の講義資料です。これを学習する大学生のために、以下の2点を作成してください。
    語尾は「〜だ」「〜である」調で統一し、無駄な装飾や会話的な表現は避けて簡潔に記述してください。

    1. 全体の要約（箇条書きで3〜5つ程度にストレートにまとめる）
    2. 重要な専門用語のピックアップと、その簡潔な解説（箇条書き）

    【講義資料のテキスト】
    {text}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def generate_questions_only(text):
    prompt = f"""
    以下の講義資料を基に、学習者の理解度を測る重要な確認問題を「3問」作成してください。
    語尾は「〜だ」「〜である」調で統一し、簡潔に記述してください。
    解答や解説はここには含めず、問題文（1., 2., 3.）のみを出力してください。

    【講義資料のテキスト】
    {text}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def grade_user_answers(text, questions, ans1, ans2, ans3):
    prompt = f"""
    あなたは大学の教授です。講義資料と出題された問題に対して、学生が入力した解答を厳格に採点し、フィードバックを行ってください。
    語尾は「〜だ」「〜である」調で統一し、簡潔に記述してください。

    【講義資料】
    {text}

    【出題された問題】
    {questions}

    【学生の解答】
    1番の問題への解答: {ans1}
    2番の問題への解答: {ans2}
    3番の問題への解答: {ans3}

    各問題に対して、以下の項目を簡潔に記述してください。
    ・正誤判定（正解、不十分、不正解など）
    ・模範解答と、学生の解答に対する具体的な改善点や解説
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text
# ---------------------------------------------

st.title("📚 大学生向け学習サポートアプリ")
st.write("講義資料（PDF）をアップロードすると、AIが要約と記述式テストを作成します。")

uploaded_file = st.file_uploader("PDFファイルを選択", type="pdf")

if uploaded_file is not None:
    # 別のファイルがアップロードされたら過去のテスト状態をリセット
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.questions = None
        st.session_state.grading_result = None
        st.session_state.current_file = uploaded_file.name

    # PDFからテキストを抽出
    reader = PdfReader(uploaded_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    
    if extracted_text.strip():
        st.success("📄 資料の読み込みに成功しました！")
        
        # 1. 要約の表示
        st.subheader("💡 AIによる要約と解説")
        with st.spinner("要約を作成中..."):
            summary = generate_summary(extracted_text)
            st.write(summary)
            
        st.divider()

        # 2. テキスト生成機能
        st.subheader("📝 記述式チェックテスト")
        st.write("資料を読んだらテストに挑戦しよう。解答を入力して採点ボタンを押してください。")
        
        # テキスト作成ボタン
        if st.button("この資料からテストを作成する"):
            with st.spinner("問題を生成中..."):
                st.session_state.questions = generate_questions_only(extracted_text)
                st.session_state.grading_result = None  # 新しい問題にしたら採点結果は消す
        
        # 問題がすでに生成されている場合、解答欄を表示
        if st.session_state.questions:
            st.info("⚠️ 解答を入力中、または採点ボタンを押す前に「テストを作成する」ボタンを再度押すと、問題が変わり入力内容が消えるので注意してください。")
            
            st.markdown("### 【問題】")
            st.write(st.session_state.questions)
            
            # 解答入力フォーム
            st.markdown("### 【あなたの解答】")
            user_ans1 = st.text_area("問題1への解答", key="ans1", placeholder="ここに解答を入力してください")
            user_ans2 = st.text_area("問題2への解答", key="ans2", placeholder="ここに解答を入力してください")
            user_ans3 = st.text_area("問題3への解答", key="ans3", placeholder="ここに解答を入力してください")
            
            # 採点ボタン
            if st.button("解答を送信して採点する"):
                with st.spinner("AI教授が採点中..."):
                    st.session_state.grading_result = grade_user_answers(
                        extracted_text, 
                        st.session_state.questions, 
                        user_ans1, 
                        user_ans2, 
                        user_ans3
                    )
            
            # 採点結果の表示
            if st.session_state.grading_result:
                st.subheader("💯 採点結果とフィードバック")
                st.write(st.session_state.grading_result)
                    
        with st.expander("元の抽出テキストを確認する"):
            st.text_area("資料の内容", extracted_text, height=200)
            
    else:
        st.warning("テキストを抽出できませんでした。")
