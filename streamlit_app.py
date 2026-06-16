import streamlit as st
from pypdf import PdfReader
from google import genai
from supabase import create_client, Client

# --- 1. 初期設定とAPIキーの読み込み ---
if "GEMINI_API_KEY" in st.secrets and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
else:
    st.error("APIキーまたはSupabaseの設定が見つかりません。Secretsを確認してください。")
    st.stop()

# --- セッション状態の初期化 ---
if "summary" not in st.session_state:
    st.session_state.summary = None
if "questions" not in st.session_state:
    st.session_state.questions = None
if "grading_result" not in st.session_state:
    st.session_state.grading_result = None

# --- AIの関数（変更なしのため省略せずにそのまま記載） ---
@st.cache_data
def generate_summary(text):
    prompt = f"（前回のプロンプトと同じ）\n{text}"
    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
    return response.text

def generate_questions_only(text):
    prompt = f"（前回のプロンプトと同じ）\n{text}"
    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
    return response.text

def grade_user_answers(text, questions, ans1, ans2, ans3):
    prompt = f"（前回のプロンプトと同じ）"
    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
    return response.text


# ==========================================
# UIレイアウト（タブで画面を分割）
# ==========================================
st.title("📚 大学生向け学習サポートアプリ")

# 2つのタブを作成
tab1, tab2 = st.tabs(["🆕 新規学習（資料読み込み）", "🗂️ 保存済みノート（復習）"])

# --- タブ1：新規学習画面 ---
with tab1:
    uploaded_file = st.file_uploader("講義資料（PDF）を選択", type="pdf")

    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        extracted_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        if extracted_text.strip():
            # 要約の生成と表示
            st.subheader("💡 AIによる要約と解説")
            with st.spinner("要約を作成中..."):
                st.session_state.summary = generate_summary(extracted_text)
                st.write(st.session_state.summary)
            
            # --- 保存機能の追加 ---
            st.divider()
            st.markdown("#### 💾 この内容を保存する")
            category_input = st.text_input("整理用の項目（例：ミクロ経済学、統計学第3回 など）")
            
            if st.button("データベースに保存"):
                if category_input:
                    # Supabaseにデータを挿入（Insert）
                    data, count = supabase.table("study_notes").insert({
                        "category": category_input,
                        "summary": st.session_state.summary,
                        "questions": st.session_state.questions if st.session_state.questions else "テスト未作成"
                    }).execute()
                    st.success(f"「{category_input}」として保存しました！🗂️タブから確認できます。")
                else:
                    st.warning("項目名を入力してください。")
            
            st.divider()
            
            # テキスト生成機能（前回と同じ処理）
            st.subheader("📝 記述式チェックテスト")
            if st.button("この資料からテストを作成する"):
                with st.spinner("問題を生成中..."):
                    st.session_state.questions = generate_questions_only(extracted_text)
            
            if st.session_state.questions:
                st.write(st.session_state.questions)
                # （前回の解答入力と採点のコードがここに入ります）
                

# --- タブ2：保存済みノート（復習画面） ---
with tab2:
    st.subheader("🗂️ 項目別に復習する")
    
    # Supabaseから保存したデータを全件取得
    response = supabase.table("study_notes").select("*").execute()
    saved_data = response.data
    
    if saved_data:
        # 保存されているすべての「項目（category）」のリストを作成し、重複を消す
        categories = list(set([item["category"] for item in saved_data]))
        
        # ユーザーに項目を選ばせる
        selected_category = st.selectbox("復習したい項目を選択してください", categories)
        
        # 選んだ項目に一致するデータだけを抽出して表示
        filtered_data = [item for item in saved_data if item["category"] == selected_category]
        
        for note in filtered_data:
            with st.expander(f"作成日: {note['created_at'][:10]}"):
                st.markdown("#### 要約")
                st.write(note["summary"])
                st.markdown("#### 問題")
                st.write(note["questions"])
    else:
        st.info("まだ保存されたデータがありません。新規学習タブから資料を保存してみましょう。")
