import os
import json
import pandas as pd

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "gsssb_question_bank.xlsx")

COLUMNS = [
    "ID", "Subject", "Question_GU", "Options_GU",
    "Question_EN", "Options_EN", "Correct_Answer", "Difficulty"
]

SUBJECTS = [
    "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
    "Mathematics (ગણિત)",
    "Reasoning (રિઝનિંગ)",
    "Gujarati Grammar (ગુજરાતી વ્યાકરણ)",
    "English Grammar (ઇંગ્લિશ વ્યાકરણ)",
    "Current Affairs (ચાલુ વર્તમાન પ્રવાહો)"
]

def init_db(excel_path=EXCEL_FILE):
    """Ensure gsssb_question_bank.xlsx exists with proper sheets without wiping existing content."""
    if not os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            pd.DataFrame(columns=COLUMNS).to_excel(writer, sheet_name="Question_Bank", index=False)
            pd.DataFrame(columns=COLUMNS).to_excel(writer, sheet_name="Revision_Sheet", index=False)
            pd.DataFrame(columns=["Timestamp", "Subject", "Total_Questions", "Score", "Correct_Count", "Incorrect_Count", "Unattempted_Count"]).to_excel(writer, sheet_name="Test_History", index=False)

def load_questions(sheet_name="Question_Bank", excel_path=EXCEL_FILE):
    """Load questions from Excel while preserving all existing records."""
    init_db(excel_path)
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        # Ensure required columns exist
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        print(f"Error loading sheet {sheet_name}: {e}")
        return pd.DataFrame(columns=COLUMNS)

def parse_options(options_raw):
    """Safely parse JSON or delimited option strings."""
    if isinstance(options_raw, list):
        return options_raw
    if isinstance(options_raw, str):
        try:
            parsed = json.loads(options_raw)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        delimiter = "|" if "|" in options_raw else (";" if ";" in options_raw else None)
        if delimiter:
            return [opt.strip() for opt in options_raw.split(delimiter)]
    return [str(options_raw)]

def save_new_questions(new_questions_list, sheet_name="Question_Bank", excel_path=EXCEL_FILE):
    """
    Append new MCQs into gsssb_question_bank.xlsx while preserving all existing questions intact.
    Filters out exact duplicate question texts.
    """
    init_db(excel_path)
    existing_df = load_questions(sheet_name, excel_path)
    
    # Track existing questions to prevent duplicates
    existing_q_gu = set()
    existing_q_en = set()
    if not existing_df.empty:
        if "Question_GU" in existing_df.columns:
            existing_q_gu = set(existing_df["Question_GU"].dropna().astype(str).str.strip().tolist())
        if "Question_EN" in existing_df.columns:
            existing_q_en = set(existing_df["Question_EN"].dropna().astype(str).str.strip().tolist())

    start_id = 1
    if not existing_df.empty and "ID" in existing_df.columns:
        valid_ids = pd.to_numeric(existing_df["ID"], errors="coerce").dropna()
        if not valid_ids.empty:
            start_id = int(valid_ids.max()) + 1

    formatted_rows = []
    added_count = 0
    
    for q in new_questions_list:
        q_gu = str(q.get("Question_GU", "")).strip()
        q_en = str(q.get("Question_EN", "")).strip()
        
        # Skip if exact question text already exists
        if (q_gu and q_gu in existing_q_gu) or (q_en and q_en in existing_q_en):
            continue

        opts_gu = json.dumps(q.get("Options_GU", []), ensure_ascii=False) if isinstance(q.get("Options_GU"), list) else q.get("Options_GU", "")
        opts_en = json.dumps(q.get("Options_EN", []), ensure_ascii=False) if isinstance(q.get("Options_EN"), list) else q.get("Options_EN", "")
        
        formatted_rows.append({
            "ID": q.get("ID", start_id + added_count),
            "Subject": q.get("Subject", "Apparel & Fashion Design (ફેશન ડિઝાઇન)"),
            "Question_GU": q_gu,
            "Options_GU": opts_gu,
            "Question_EN": q_en,
            "Options_EN": opts_en,
            "Correct_Answer": str(q.get("Correct_Answer", "A")).upper().strip(),
            "Difficulty": q.get("Difficulty", "Medium")
        })
        
        if q_gu: existing_q_gu.add(q_gu)
        if q_en: existing_q_en.add(q_en)
        added_count += 1

    if not formatted_rows:
        return 0

    new_df = pd.DataFrame(formatted_rows)
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    _write_all(excel_path, 
               updated_df if sheet_name == "Question_Bank" else load_questions("Question_Bank", excel_path),
               updated_df if sheet_name == "Revision_Sheet" else load_questions("Revision_Sheet", excel_path))
    return len(formatted_rows)

def merge_uploaded_excel(uploaded_file, excel_path=EXCEL_FILE):
    """
    Import and merge custom uploaded Excel file into gsssb_question_bank.xlsx without losing existing questions.
    """
    try:
        df_uploaded = pd.read_excel(uploaded_file)
        if df_uploaded.empty:
            return 0, "Uploaded Excel file is empty."
            
        questions_dict_list = df_uploaded.to_dict("records")
        saved_count = save_new_questions(questions_dict_list, sheet_name="Question_Bank", excel_path=excel_path)
        return saved_count, f"Successfully merged {saved_count} new questions into database!"
    except Exception as e:
        return 0, f"Error reading uploaded Excel file: {str(e)}"

def save_revision_questions(wrong_df, excel_path=EXCEL_FILE):
    """Append wrong questions to Revision_Sheet without duplicates."""
    if wrong_df.empty:
        return 0
    init_db(excel_path)
    rev_df = load_questions("Revision_Sheet", excel_path)
    
    if not rev_df.empty and "Question_GU" in rev_df.columns:
        existing_q = set(rev_df["Question_GU"].dropna().astype(str).str.strip().tolist())
        wrong_df = wrong_df[~wrong_df["Question_GU"].dropna().astype(str).str.strip().isin(existing_q)]
        
    if wrong_df.empty:
        return 0
        
    combined = pd.concat([rev_df, wrong_df], ignore_index=True)
    _write_all(excel_path, load_questions("Question_Bank", excel_path), combined)
    return len(wrong_df)

def save_test_result(timestamp, subject, total, score, correct, incorrect, unattempted, excel_path=EXCEL_FILE):
    """Log test score result into Test_History sheet."""
    init_db(excel_path)
    try:
        try:
            hist_df = pd.read_excel(excel_path, sheet_name="Test_History")
        except Exception:
            hist_df = pd.DataFrame()
            
        new_entry = pd.DataFrame([{
            "Timestamp": timestamp, "Subject": subject, "Total_Questions": total,
            "Score": score, "Correct_Count": correct, "Incorrect_Count": incorrect, "Unattempted_Count": unattempted
        }])
        hist_updated = pd.concat([hist_df, new_entry], ignore_index=True)
        _write_all(excel_path, load_questions("Question_Bank", excel_path), load_questions("Revision_Sheet", excel_path), hist_updated)
    except Exception as e:
        print(f"Result save notice: {e}")

def _write_all(excel_path, bank_df, rev_df, hist_df=None):
    """Internal helper preserving all Excel sheets during write."""
    if hist_df is None:
        try:
            hist_df = pd.read_excel(excel_path, sheet_name="Test_History")
        except Exception:
            hist_df = pd.DataFrame()
            
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        bank_df.to_excel(writer, sheet_name="Question_Bank", index=False)
        rev_df.to_excel(writer, sheet_name="Revision_Sheet", index=False)
        hist_df.to_excel(writer, sheet_name="Test_History", index=False)
