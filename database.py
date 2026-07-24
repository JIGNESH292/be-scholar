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
    """Ensure Excel database file exists with required sheets."""
    if not os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            pd.DataFrame(columns=COLUMNS).to_excel(writer, sheet_name="Question_Bank", index=False)
            pd.DataFrame(columns=COLUMNS).to_excel(writer, sheet_name="Revision_Sheet", index=False)
            pd.DataFrame(columns=["Timestamp", "Subject", "Total_Questions", "Score", "Correct_Count", "Incorrect_Count", "Unattempted_Count"]).to_excel(writer, sheet_name="Test_History", index=False)

def load_questions(sheet_name="Question_Bank", excel_path=EXCEL_FILE):
    """Load question DataFrame from Excel sheet safely."""
    init_db(excel_path)
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        return df if not df.empty else pd.DataFrame(columns=COLUMNS)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def parse_options(options_raw):
    """Cleanly parse option strings or list representations."""
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
    """Save new MCQs into Excel dataframe."""
    init_db(excel_path)
    existing = load_questions(sheet_name, excel_path)
    
    start_id = 1
    if not existing.empty and "ID" in existing.columns:
        valid_ids = pd.to_numeric(existing["ID"], errors="coerce").dropna()
        if not valid_ids.empty:
            start_id = int(valid_ids.max()) + 1

    formatted = []
    for idx, q in enumerate(new_questions_list):
        opts_gu = json.dumps(q.get("Options_GU", []), ensure_ascii=False) if isinstance(q.get("Options_GU"), list) else q.get("Options_GU", "")
        opts_en = json.dumps(q.get("Options_EN", []), ensure_ascii=False) if isinstance(q.get("Options_EN"), list) else q.get("Options_EN", "")
        formatted.append({
            "ID": q.get("ID", start_id + idx),
            "Subject": q.get("Subject", "Apparel & Fashion Design (ફેશન ડિઝાઇન)"),
            "Question_GU": q.get("Question_GU", ""),
            "Options_GU": opts_gu,
            "Question_EN": q.get("Question_EN", ""),
            "Options_EN": opts_en,
            "Correct_Answer": str(q.get("Correct_Answer", "A")).upper().strip(),
            "Difficulty": q.get("Difficulty", "Medium")
        })

    updated = pd.concat([existing, pd.DataFrame(formatted)], ignore_index=True)
    _write_all(excel_path, updated if sheet_name == "Question_Bank" else load_questions("Question_Bank", excel_path),
               updated if sheet_name == "Revision_Sheet" else load_questions("Revision_Sheet", excel_path))
    return len(formatted)

def save_revision_questions(wrong_df, excel_path=EXCEL_FILE):
    """Append wrong questions to Revision_Sheet without duplicates."""
    if wrong_df.empty:
        return 0
    init_db(excel_path)
    rev_df = load_questions("Revision_Sheet", excel_path)
    
    if not rev_df.empty and "Question_GU" in rev_df.columns:
        existing_q = set(rev_df["Question_GU"].astype(str).tolist())
        wrong_df = wrong_df[~wrong_df["Question_GU"].astype(str).isin(existing_q)]
        
    if wrong_df.empty:
        return 0
        
    combined = pd.concat([rev_df, wrong_df], ignore_index=True)
    _write_all(excel_path, load_questions("Question_Bank", excel_path), combined)
    return len(wrong_df)

def save_test_result(timestamp, subject, total, score, correct, incorrect, unattempted, excel_path=EXCEL_FILE):
    """Log test score result."""
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
    """Internal write helper preserving all sheets."""
    if hist_df is None:
        try:
            hist_df = pd.read_excel(excel_path, sheet_name="Test_History")
        except Exception:
            hist_df = pd.DataFrame()
            
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        bank_df.to_excel(writer, sheet_name="Question_Bank", index=False)
        rev_df.to_excel(writer, sheet_name="Revision_Sheet", index=False)
        hist_df.to_excel(writer, sheet_name="Test_History", index=False)
