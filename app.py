import os
import json
import time
import datetime
import io
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import database as db
import pdf_extractor as pe
import ai_generator as ai

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

AUTH_USER = "jigneshpatel"
AUTH_PASS = "jigishapatel"

def get_active_api_key():
    """Secure & robust API Key retrieval."""
    for widget_key in ["inline_key_input", "sidebar_key_input", "gemini_api_key"]:
        val = st.session_state.get(widget_key, "")
        if val and str(val).strip():
            return str(val).strip()
            
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            sec_val = str(st.secrets["GEMINI_API_KEY"]).strip()
            if sec_val:
                return sec_val
    except Exception:
        pass

    env_val = os.getenv("GEMINI_API_KEY", "").strip()
    if env_val:
        return env_val

    return ""

@st.cache_data(ttl=3)
def get_cached_questions(sheet_name="Question_Bank"):
    """Cache Excel data in memory for 3x faster UI rendering."""
    return db.load_questions(sheet_name)

# Page Setup
st.set_page_config(page_title="Be Scholar - GSSSB Exam Prep", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# Lightweight Custom CSS
st.markdown("""
<style>
    .main-title { color: #1E88E5; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.1rem; }
    .sub-title { color: #424242; font-size: 1.1rem; margin-bottom: 0.4rem; }
    .author-badge { background-color: #E3F2FD; border-left: 4px solid #1E88E5; padding: 8px 12px; border-radius: 6px; color: #0D47A1; font-weight: 600; font-size: 0.85rem; line-height: 1.4; margin-bottom: 1rem; }
    .login-card { max-width: 450px; margin: 40px auto; padding: 2rem; background-color: #FFFFFF; border-radius: 10px; border-top: 5px solid #1E88E5; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .card { background-color: #f8f9fa; border-left: 5px solid #1E88E5; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .timer-badge { background-color: #E3F2FD; color: #0D47A1; padding: 6px 14px; border-radius: 18px; font-weight: bold; font-size: 1.1rem; border: 1px solid #90CAF9; }
</style>
""", unsafe_allow_html=True)

# Session State Init
for k, v in [("authenticated", False), ("lang", "GU"), ("quiz_active", False), ("quiz_questions", []), ("user_answers", {}), ("marked_questions", set()), ("current_q_idx", 0), ("start_time", None), ("test_submitted", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

db.init_db()

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <img src="https://img.icons8.com/color/96/graduation-cap.png" width="80">
            <h1 style="color: #1E88E5; font-weight: 800; margin-bottom: 0;">🎓 Be Scholar</h1>
            <p style="color: #555555; font-size: 1.1rem;">GSSSB Supervisor Instructor Exam Prep</p>
            <div class="author-badge" style="text-align: left; display: inline-block;">
                DEVELOPED BY DR.JIGNESH B.PATEL,<br>
                ASSISTANT PROFESSOR,<br>
                DC & IT,<br>
                HNGU ,PATAN
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("🔐 લૉગિન / Login Access")
            user_in = st.text_input("Username / યુઝરનેમ:", placeholder="Enter Username")
            pass_in = st.text_input("Password / પાસવર્ડ:", type="password", placeholder="Enter Password")
            
            submit_login = st.form_submit_button("🔐 Login / પ્રવેશ કરો", use_container_width=True, type="primary")
            
            if submit_login:
                if user_in.strip() == AUTH_USER and pass_in.strip() == AUTH_PASS:
                    st.session_state.authenticated = True
                    st.success("✅ લૉગિન સફળ થયું!")
                    st.rerun()
                else:
                    st.error("❌ અમાન્ય યુઝરનેમ અથવા પાસવર્ડ! (Invalid Username or Password)")
    st.stop()


# --- SIDEBAR (AUTHENTICATED) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/graduation-cap.png", width=60)
    st.title("Be Scholar")
    st.caption("GSSSB Supervisor Instructor Exam Prep")
    st.markdown('<div class="author-badge">👨‍🏫 DEVELOPED BY DR.JIGNESH B.PATEL,<br>ASSISTANT PROFESSOR,<br>DC & IT,<br>HNGU ,PATAN</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    navigation = st.radio("મેનૂ પસંદ કરો / Select View:", [
        "🎯 Test Engine (ટેસ્ટ કસોટી)", 
        "📚 Question Bank Manager (સંચિત પ્રશ્ન સંગ્રહ)",
        "🤖 AI Bulk Generator (હજારો MCQs)", 
        "📊 Performance Analytics (ડેશબોર્ડ)", 
        "📖 Revision Zone (રિવિઝન ઝોન)", 
        "🔑 API Key Guide (મદદ અને સેટિંગ્સ)"
    ])
    st.markdown("---")
    
    sidebar_key = st.text_input("API Key પેસ્ટ કરો:", value=get_active_api_key(), type="password", key="sidebar_key_input")
    if sidebar_key and sidebar_key != st.session_state.get("gemini_api_key"):
        st.session_state.gemini_api_key = sidebar_key
        try:
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={sidebar_key}\n")
        except Exception:
            pass

    st.markdown("---")
    if st.button("🚪 Logout (લૉગઆઉટ)", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# Main Header
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    st.markdown('<div class="main-title">🎓 Be Scholar</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">GSSSB સુપરવાઈઝર ઈન્સ્ટ્રક્ટર (Apparel & Fashion Design) પરીક્ષા તૈયારી સૉફ્ટવેર</div>', unsafe_allow_html=True)
    st.markdown('<div class="author-badge">DEVELOPED BY DR.JIGNESH B.PATEL,<br>ASSISTANT PROFESSOR,<br>DC & IT,<br>HNGU ,PATAN</div>', unsafe_allow_html=True)

with c_h2:
    st.markdown("##### 🌐 ભાષા / Language:")
    toggle_val = st.radio("Lang", ["ગુજરાતી 🇮🇳", "English 🇬🇧"], index=0 if st.session_state.lang == "GU" else 1, horizontal=True, label_visibility="collapsed")
    st.session_state.lang = "GU" if "ગુજરાતી" in toggle_val else "EN"

st.markdown("---")


# ================= PAGE 1: TEST ENGINE (ZERO API TOKEN COST) =================
if navigation.startswith("🎯"):
    st.header("🎯 GSSSB કસોટી એન્જિન (Test Engine)")

    if not st.session_state.quiz_active:
        st.subheader("📋 નવી ટેસ્ટ સેટઅપ કરો (0% API Token Cost)")
        df_questions = get_cached_questions("Question_Bank")
        
        if df_questions.empty:
            st.warning("⚠️ ડેટાબેઝમાં હજુ સુધી કોઈ પ્રશ્નો નથી. પ્રાથમિક પ્રશ્નો લોડ કરવા માટે નીચેના બટન પર ક્લિક કરો.")
            if st.button("🌱 Load Initial Seed Questions Now"):
                import seed_data
                seed_data.seed_database()
                st.cache_data.clear()
                st.rerun()
        else:
            st.info(f"💡 તમારા સંગ્રહિત એક્સેલ ડેટાબેઝમાં હાલ કુલ **{len(df_questions)}** પ્રશ્નો ઉપલબ્ધ છે. કોઈપણ API Token નો ખર્ચ કર્યા વગર ટેસ્ટ આપો!")
            subjects = ["તમામ વિષયો (All Subjects)"] + list(df_questions["Subject"].dropna().unique())
            
            c1, c2, c3 = st.columns(3)
            with c1: selected_subject = st.selectbox("વિષય પસંદ કરો:", subjects)
            with c2: q_count = st.selectbox("પ્રશ્નોની સંખ્યા:", [10, 25, 50, 100, 200], index=0)
            with c3: duration_mins = st.number_input("સમય (મિનિટમાં):", min_value=5, max_value=180, value=30, step=5)

            if st.button("🚀 ટેસ્ટ શરૂ કરો (Start Test)", type="primary", use_container_width=True):
                filtered = df_questions if selected_subject.startswith("તમામ") else df_questions[df_questions["Subject"] == selected_subject]
                if filtered.empty:
                    st.error("આ વિષય માટે કોઈ પ્રશ્નો મળ્યા નથી!")
                else:
                    sample_sz = min(len(filtered), int(q_count))
                    st.session_state.quiz_questions = filtered.sample(n=sample_sz).to_dict("records")
                    st.session_state.quiz_active = True
                    st.session_state.user_answers, st.session_state.marked_questions = {}, set()
                    st.session_state.current_q_idx = 0
                    st.session_state.start_time = time.time()
                    st.session_state.test_duration = duration_mins * 60
                    st.session_state.test_submitted = False
                    st.rerun()
    else:
        questions = st.session_state.quiz_questions
        curr_idx = st.session_state.current_q_idx
        q_data = questions[curr_idx]
        
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, st.session_state.test_duration - elapsed)
        if remaining == 0 and not st.session_state.test_submitted:
            st.session_state.test_submitted = True

        col_t1, col_t2, col_t3 = st.columns([2, 2, 2])
        with col_t1:
            m, s = divmod(int(remaining), 60)
            st.markdown(f'<div class="timer-badge">⏱️ બાકી સમય: {m:02d}:{s:02d}</div>', unsafe_allow_html=True)
        with col_t2: st.markdown(f"**પ્રશ્ન ક્રમાંક:** {curr_idx + 1} / {len(questions)}")
        with col_t3:
            if st.button("📥 ટેસ્ટ સબમિટ કરો", type="primary"):
                st.session_state.test_submitted = True
                st.rerun()

        st.progress((curr_idx + 1) / len(questions))
        st.markdown("---")
        col_q, col_grid = st.columns([3, 1])

        with col_q:
            is_gu = st.session_state.lang == "GU"
            q_text = q_data.get("Question_GU") if is_gu else q_data.get("Question_EN")
            if not q_text or str(q_text) == "nan": q_text = q_data.get("Question_EN", "")
            opts = db.parse_options(q_data.get("Options_GU") if is_gu else q_data.get("Options_EN"))
            
            st.markdown(f'<div class="card"><h4>{curr_idx + 1}. {q_text}</h4><span class="badge-gu">{q_data.get("Subject")}</span></div>', unsafe_allow_html=True)

            curr_sel = st.session_state.user_answers.get(curr_idx, None)
            opt_letters = ["A", "B", "C", "D"]
            sel_letter = st.radio("જવાબ પસંદ કરો:", opt_letters, format_func=lambda i: opts[opt_letters.index(i)] if opt_letters.index(i) < len(opts) else i, index=opt_letters.index(curr_sel) if curr_sel in opt_letters else None, key=f"q_r_{curr_idx}")
            if sel_letter: st.session_state.user_answers[curr_idx] = sel_letter

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("⬅️ પાછળ", disabled=(curr_idx == 0)):
                    st.session_state.current_q_idx -= 1
                    st.rerun()
            with b2:
                if st.button("➡️ આગળ", disabled=(curr_idx == len(questions) - 1)):
                    st.session_state.current_q_idx += 1
                    st.rerun()
            with b3:
                is_m = curr_idx in st.session_state.marked_questions
                if st.button("💛 Unmark" if is_m else "⭐ Mark"):
                    st.session_state.marked_questions.remove(curr_idx) if is_m else st.session_state.marked_questions.add(curr_idx)
                    st.rerun()
            with b4:
                if st.button("❌ Clear Choice"):
                    st.session_state.user_answers.pop(curr_idx, None)
                    st.rerun()

        with col_grid:
            st.markdown("##### 📌 પ્રશ્ન ગ્રીડ")
            grid_cols = st.columns(4)
            for i in range(len(questions)):
                sym = f"⭐{i+1}" if i in st.session_state.marked_questions else (f"✅{i+1}" if i in st.session_state.user_answers else f"{i+1}")
                if i == curr_idx: sym = f"👉{sym}"
                with grid_cols[i % 4]:
                    if st.button(sym, key=f"g_{i}"):
                        st.session_state.current_q_idx = i
                        st.rerun()

        if st.session_state.test_submitted:
            st.markdown("---")
            st.header("📊 કસોટી પરિણામ")
            correct = sum(1 for idx, q in enumerate(questions) if st.session_state.user_answers.get(idx) == str(q.get("Correct_Answer", "")).upper().strip())
            unatt = sum(1 for idx in range(len(questions)) if idx not in st.session_state.user_answers)
            inc = len(questions) - correct - unatt
            score = (correct * 1.0) - (inc * 0.25)

            wrong_rows = [q for idx, q in enumerate(questions) if idx in st.session_state.user_answers and st.session_state.user_answers.get(idx) != str(q.get("Correct_Answer", "")).upper().strip()]
            if wrong_rows:
                db.save_revision_questions(pd.DataFrame(wrong_rows))
                st.cache_data.clear()

            db.save_test_result(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), questions[0].get("Subject", "General"), len(questions), score, correct, inc, unatt)

            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("કુલ ગુણ", f"{score:.2f} / {len(questions)}")
            rc2.metric("સાચા જવાબો", f"✅ {correct}")
            rc3.metric("ખોટા જવાબો (-0.25)", f"❌ {inc}")
            rc4.metric("અપ્રયત્નિત", f"⚪ {unatt}")

            if st.button("🔄 નવી ટેસ્ટ આપો", type="primary"):
                st.session_state.quiz_active = False
                st.session_state.test_submitted = False
                st.rerun()


# ================= PAGE 2: QUESTION BANK MANAGER (સંચિત પ્રશ્ન સંગ્રહ) =================
elif navigation.startswith("📚"):
    st.header("📚 Question Bank Manager (સંચિત પ્રશ્ન સંગ્રહ)")
    st.markdown("અત્યાર સુધીના તમામ સાચવેલા જૂના અને નવા પ્રશ્નોનું સંચાલન, ડાઉનલોડ અને ઓટો-બેકઅપ કન્ટ્રોલ.")
    
    df_all = get_cached_questions("Question_Bank")
    
    col_mb1, col_mb2 = st.columns([2, 1])
    with col_mb1:
        st.subheader("📥 Excel ડેટાબેઝ બેકઅપ ડાઉનલોડ કરો")
        st.markdown("બધા સંગ્રહિત પ્રશ્નો સાથેની અદ્યતન એક્સેલ ફાઈલ ડાઉનલોડ કરી તમારા કમ્પ્યુટરમાં કાયમી સેવ રાખો:")
        
        # Prepare Excel download buffer
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_all.to_excel(writer, sheet_name="Question_Bank", index=False)
            db.load_questions("Revision_Sheet").to_excel(writer, sheet_name="Revision_Sheet", index=False)
            db.load_questions("Test_History").to_excel(writer, sheet_name="Test_History", index=False)
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download gsssb_question_bank.xlsx Excel Backup",
            data=excel_data,
            file_name="gsssb_question_bank.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
    with col_mb2:
        st.subheader("📤 એક્સેલ ફાઈલ ઈમ્પોર્ટ કરો (Restore)")
        uploaded_excel_file = st.file_uploader("જૂની કે કસ્ટમ એક્સેલ ફાઈલ અપલોડ કરો:", type=["xlsx", "xls"])
        if uploaded_excel_file is not None:
            if st.button("🔄 Restore/Merge Excel Database"):
                saved_c, msg = db.merge_uploaded_excel(uploaded_excel_file)
                if saved_c > 0:
                    st.cache_data.clear()
                    st.success(f"🎉 {msg}")
                    st.rerun()
                else:
                    st.warning(f"⚠️ {msg}")

    st.markdown("---")
    st.subheader(f"🔍 સંચિત પ્રશ્નોનું બ્રાઉઝિંગ (કુલ પ્રશ્નો: {len(df_all)})")
    
    if df_all.empty:
        st.info("ડેટાબેઝમાં હજુ સુધી કોઈ પ્રશ્નો ઉપલબ્ધ નથી.")
    else:
        filter_c1, filter_c2 = st.columns([1, 1])
        with filter_c1:
            subj_filter = st.selectbox("વિષય અનુસાર ફિલ્ટર કરો:", ["તમામ વિષયો (All)"] + list(df_all["Subject"].dropna().unique()))
        with filter_c2:
            search_query = st.text_input("પ્રશ્નમાં શબ્દ શોધો (Search Text):")

        df_view = df_all.copy()
        if subj_filter != "તમામ વિષયો (All)":
            df_view = df_view[df_view["Subject"] == subj_filter]
        if search_query.strip():
            df_view = df_view[
                df_view["Question_GU"].astype(str).str.contains(search_query, case=False, na=False) |
                df_view["Question_EN"].astype(str).str.contains(search_query, case=False, na=False)
            ]

        st.caption(f"દર્શાવેલ પ્રશ્નો: {len(df_view)} / {len(df_all)}")
        st.dataframe(df_view[["ID", "Subject", "Question_GU", "Question_EN", "Correct_Answer", "Difficulty"]], use_container_width=True)


# ================= PAGE 3: FLEXIBLE AI BULK MCQ GENERATOR =================
elif navigation.startswith("🤖"):
    st.header("🤖 AI બલ્ક પ્રશ્ન નિર્માણ મોડ્યુલ (Flexible MCQ Generator)")
    st.markdown("તમારી જરૂરિયાત અનુસાર **મુક્ત સંખ્યામાં (૧૦ થી ૧૦૦૦+ )** નવેનવા દ્વિભાષી પ્રશ્નો ઓટો-જનરેટ કરી `gsssb_question_bank.xlsx` માં ઉમેરો.")

    active_key = get_active_api_key()
    
    st.subheader("🔑 API Key સેટઅપ")
    ck1, ck2 = st.columns([3, 1])
    with ck1: in_key = st.text_input("API Key:", value=active_key, type="password", key="inline_key_input")
    with ck2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔑 Save API Key", type="primary"):
            if in_key.strip():
                st.session_state.gemini_api_key = in_key.strip()
                try:
                    with open(ENV_PATH, "w", encoding="utf-8") as f: f.write(f"GEMINI_API_KEY={in_key.strip()}\n")
                except Exception: pass
                st.success("✅ API Key સાચવી લેવાઈ!")
                st.rerun()

    st.markdown("---")
    ca1, ca2 = st.columns([1, 1])
    with ca1:
        uploaded_pdfs = st.file_uploader("GSSSB જૂના પેપર્સ PDFs અપલોડ કરો:", type=["pdf"], accept_multiple_files=True)
        url_in = st.text_input("અથવા Web URL:")
        custom_txt = st.text_area("અથવા કસ્ટમ ટેક્સ્ટ:", height=100)
    with ca2:
        target_subject = st.selectbox("લક્ષ્ય વિષય:", db.SUBJECTS)
        
        gen_mode = st.radio("પ્રશ્નોની સંખ્યા સિલેક્શન મોડ:", ["પસંદગી સ્લાઇડર (Preset)", "કસ્ટમ સંખ્યા (Custom Input)"], horizontal=True)
        if gen_mode == "પસંદગી સ્લાઇડર (Preset)":
            target_total = st.select_slider("🎯 કેટલા પ્રશ્નો જનરેટ કરવા છે?", options=[5, 10, 20, 50, 100, 250, 500, 1000], value=20)
        else:
            target_total = st.number_input("🎯 કસ્ટમ પ્રશ્નોની સંખ્યા દાખલ કરો:", min_value=1, max_value=2000, value=15, step=5)
            
        batch_size = st.slider("Batch Size (દર API કૉલે પ્રશ્નો):", min_value=5, max_value=30, value=15)

    if st.button(f"⚡ {target_total} નવા દ્વિભાષી MCQs ઓટો-જનરેટ કરી એક્સેલમાં ઉમેરો", type="primary", use_container_width=True):
        final_k = get_active_api_key()
        if not final_k:
            st.error("❌ API Key ગેરહાજર છે! સાઈડબાર કે ઉપરના ખાનામાં API Key દાખલ કરો.")
        else:
            all_chunks = []
            if uploaded_pdfs:
                for pdf in uploaded_pdfs: all_chunks.extend(pe.extract_pdf_chunks(pdf))
            elif url_in: all_chunks.append(pe.extract_text_from_url(url_in))
            elif custom_txt: all_chunks.append(custom_txt)
            else: all_chunks.append(f"GSSSB Supervisor Instructor syllabus for {target_subject}.")

            pbar, stxt = st.progress(0.0), st.empty()
            def on_prog(cur, tot, batch, bnum):
                pbar.progress(min(1.0, cur / tot))
                stxt.markdown(f"⏳ **પેકેટ {bnum} પૂર્ણ:** જનરેટ થાઈ કાયમી ઉમેરાયા: **{cur} / {tot}** MCQs...")

            succ, msg, gen_list = ai.generate_bulk_gsssb_mcqs(final_k, all_chunks, target_subject, target_total, batch_size, on_prog)
            if succ:
                st.cache_data.clear() # Invalidate cache so new questions reflect everywhere immediately
                st.balloons()
                st.success(f"🎉 {msg}")
                st.info("💡 આ પ્રશ્નો અગાઉના જૂના પ્રશ્નો સાથે અકબંધ રીતે 'gsssb_question_bank.xlsx' માં ઉમેરાઈ ગયા છે!")
            else:
                st.error(msg)


# ================= PAGE 4: PERFORMANCE ANALYTICS =================
elif navigation.startswith("📊"):
    st.header("📊 પ્રગતિ ડેશબોર્ડ")
    df_hist = db.load_questions("Test_History")
    df_q = get_cached_questions("Question_Bank")
    df_r = get_cached_questions("Revision_Sheet")
    
    s1, s2, s3 = st.columns(3)
    s1.metric("કુલ ડેટાબેઝ પ્રશ્નો", len(df_q))
    s2.metric("કુલ આપેલી ટેસ્ટ", len(df_hist))
    s3.metric("રિવિઝન પેન્ડિંગ પ્રશ્નો", len(df_r))
    st.markdown("---")

    if df_hist.empty:
        st.info("ℹ️ હજુ સુધી કોઈ કસોટી પૂરી થઈ નથી.")
    else:
        import plotly.express as px
        subj_summary = df_hist.groupby("Subject")[["Score", "Correct_Count", "Incorrect_Count"]].sum().reset_index()
        fig = px.bar(subj_summary, x="Subject", y=["Correct_Count", "Incorrect_Count"], title="વિષયવાર સચોટતા", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_hist.sort_values(by="Timestamp", ascending=False), use_container_width=True)


# ================= PAGE 5: REVISION ZONE =================
elif navigation.startswith("📖"):
    st.header("📖 રિવિઝન ઝોન")
    df_rev = get_cached_questions("Revision_Sheet")
    
    if df_rev.empty:
        st.success("🎉 તમારી રિવિઝન શીટ ખાલી છે.")
    else:
        st.warning(f"⚠️ તમારી રિવિઝન શીટમાં કુલ **{len(df_rev)}** ખોટા પડેલા પ્રશ્નો છે.")
        if st.button("🚀 રિવિઝન કસોટી શરૂ કરો", type="primary"):
            st.session_state.quiz_questions = df_rev.to_dict("records")
            st.session_state.quiz_active = True
            st.session_state.user_answers, st.session_state.marked_questions = {}, set()
            st.session_state.current_q_idx = 0
            st.session_state.start_time = time.time()
            st.session_state.test_duration = 3600
            st.session_state.test_submitted = False
            st.rerun()

        is_gu = st.session_state.lang == "GU"
        for idx, r in df_rev.iterrows():
            with st.expander(f"📌 [{r['Subject']}] {r['Question_GU'] if is_gu else r['Question_EN']}"):
                st.write(f"**સાચો જવાબ:** {r['Correct_Answer']}")
                st.write("**વિકલ્પો:**", db.parse_options(r['Options_GU'] if is_gu else r['Options_EN']))


# ================= PAGE 6: HELP & GUIDE =================
else:
    st.header("🔑 ગાઈડ અને સેટિંગ્સ")
    st.markdown("""
    ### 🎓 Be Scholar - GSSSB Supervisor Instructor Exam Software
    **DEVELOPED BY DR.JIGNESH B.PATEL,**  
    **ASSISTANT PROFESSOR,**  
    **DC & IT,**  
    **HNGU ,PATAN**
    ---
    1. **ઝીરો API Token ટેસ્ટિંગ**: એકવાર સેવ થયેલા પ્રશ્નોમાંથી ૧૦૦% મફતમાં અનંતવાર ટેસ્ટ આપો.
    2. **કસ્ટમ AI MCQs નિર્માણ**: તમને જોઈએ તેટલા જનરેટ કરી કાયમી એક્સેલમાં ઉમેરો.
    3. **Excel ડાઉનલોડ & અપલોડ**: **📚 Question Bank Manager** મેનૂમાંથી એક્સેલ ડાઉનલોડ કે ઓટો-ઈમ્પોર્ટ કરો.
    """)
