import json
import re
import time
import database as db

# 100% Verified working Google Gemini API models
VERIFIED_GEMINI_MODELS = [
    'gemini-flash-lite-latest',
    'gemini-flash-latest',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-2.0-flash'
]

def clean_and_parse_json(raw_text):
    """
    Robust multi-pass JSON parser that handles raw unescaped backslashes,
    control characters, and markdown formatting from LLM outputs without crashing.
    """
    if not raw_text:
        return None

    # Extract JSON array substring [ ... ]
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    clean = match.group(0) if match else raw_text.strip().strip("```json").strip("```").strip()

    # Pass 1: Direct JSON load with non-strict mode (allows unescaped control chars)
    try:
        return json.loads(clean, strict=False)
    except Exception:
        pass

    # Pass 2: Fix raw invalid backslashes (replace single \ not part of valid JSON escapes)
    sanitized = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', clean)
    try:
        return json.loads(sanitized, strict=False)
    except Exception:
        pass

    # Pass 3: Aggressive backslash sanitization
    sanitized_aggressive = clean.replace('\\', '\\\\').replace('\\\\"', '\\"')
    try:
        return json.loads(sanitized_aggressive, strict=False)
    except Exception:
        return None

def generate_gsssb_mcqs(api_key, context_text, subject="Apparel & Fashion Design (ફેશન ડિઝાઇન)", num_questions=10):
    """
    Generate bilingual GSSSB MCQs using Google Gemini API or OpenAI API cleanly.
    Uses robust JSON parsing and error handling.
    """
    if not api_key:
        return False, "API Key missing!"

    api_key = api_key.strip()
    if api_key.startswith("your_api_key") or len(api_key) < 10:
        return False, "કૃપા કરીને સાચી Google Gemini API Key દાખલ કરો."

    prompt = f"""
You are an expert exam question creator for GSSSB (Gujarat Subordinate Service Selection Board) Supervisor Instructor (Apparel & Fashion Design) examination.

Analyze reference text and create exactly {num_questions} NEW, high-quality, GSSSB-level MCQs.
Target Subject: {subject}

RULES:
1. Questions & 4 Options in both Gujarati (Question_GU, Options_GU) and English (Question_EN, Options_EN).
2. Correct_Answer: "A", "B", "C", or "D".
3. Difficulty: "Easy", "Medium", or "Hard".
4. Do NOT use unescaped backslashes inside JSON strings.
5. Return ONLY a valid JSON array of objects.

[
  {{
    "Subject": "{subject}",
    "Question_GU": "ગુજરાતી પ્રશ્ન...",
    "Options_GU": ["A) વિકલ્પ ૧", "B) વિકલ્પ ૨", "C) વિકલ્પ ૩", "D) વિકલ્પ ૪"],
    "Question_EN": "English Question...",
    "Options_EN": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "Correct_Answer": "A",
    "Difficulty": "Medium"
  }}
]

Text:
{context_text[:8000]}
"""

    raw_response = ""
    is_openai = api_key.startswith("sk-") and not api_key.startswith("AQ.")

    if is_openai:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": prompt}],
                temperature=0.7
            )
            raw_response = resp.choices[0].message.content
        except Exception as e:
            return False, f"OpenAI API Error: {str(e)}"
    else:
        # Google Gemini API Execution
        last_err = ""
        
        # 1. Primary: Modern google-genai SDK
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            for m in VERIFIED_GEMINI_MODELS:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        raw_response = resp.text
                        break
                except Exception as err_m:
                    last_err = str(err_m)
        except Exception as e_modern:
            last_err = str(e_modern)

        # 2. Fallback: Legacy google-generativeai SDK if modern SDK fails
        if not raw_response:
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                for m_legacy in VERIFIED_GEMINI_MODELS:
                    try:
                        g_model = genai_legacy.GenerativeModel(m_legacy)
                        res = g_model.generate_content(prompt)
                        if res and res.text:
                            raw_response = res.text
                            break
                    except Exception as err_l:
                        last_err = str(err_l)
            except (ImportError, ModuleNotFoundError):
                pass
            except Exception as e_l:
                last_err = str(e_l)

        if not raw_response:
            return False, f"Gemini API Error: {last_err}"

    parsed = clean_and_parse_json(raw_response)
    if parsed and isinstance(parsed, list) and len(parsed) > 0:
        return True, parsed
        
    return False, f"Parsing Exception: Could not parse response. Snippet: {raw_response[:150]}"

def generate_bulk_gsssb_mcqs(api_key, text_chunks, subject="Apparel & Fashion Design (ફેશન ડિઝાઇન)", target_total=100, batch_size=20, progress_callback=None):
    """
    Bulk Question Generator looping seamlessly in batches with auto-retry and non-halting resilience.
    """
    if not api_key:
        return False, "API Key missing!", []

    if not text_chunks:
        text_chunks = [f"GSSSB Supervisor Instructor exam syllabus for {subject}."]

    total_gen = 0
    all_gen = []
    chunk_idx = 0
    batch_count = 0
    failed_attempts = 0
    num_chunks = len(text_chunks)

    while total_gen < target_total:
        needed = min(batch_size, target_total - total_gen)
        batch_count += 1
        
        success, result = generate_gsssb_mcqs(api_key, text_chunks[chunk_idx % num_chunks], subject, needed)
        
        if success and isinstance(result, list):
            saved = db.save_new_questions(result, "Question_Bank")
            total_gen += saved
            all_gen.extend(result)
            failed_attempts = 0 # Reset failed attempts on success
            
            if progress_callback:
                progress_callback(total_gen, target_total, result, batch_count)
            chunk_idx += 1
            time.sleep(1)
        else:
            # Check for critical API key or auth errors
            if "API Key" in str(result) or "403" in str(result) or "401" in str(result):
                return False, f"❌ {result}", all_gen
                
            failed_attempts += 1
            time.sleep(1.5)
            chunk_idx += 1
            
            # If total batch attempts exceeds 3x total batches, return whatever questions were saved without erroring out
            if batch_count > (target_total // max(1, batch_size)) * 3 + 10 or failed_attempts > 8:
                if total_gen > 0:
                    return True, f"Generated and saved {total_gen} MCQs into Excel database!", all_gen
                else:
                    return False, f"❌ Generation paused: {result}", all_gen

    return True, f"Successfully generated and saved {total_gen} MCQs in {batch_count} batches!", all_gen
