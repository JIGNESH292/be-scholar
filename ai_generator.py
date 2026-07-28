import json
import re
import time
import database as db

def generate_gsssb_mcqs(api_key, context_text, subject="Apparel & Fashion Design (ફેશન ડિઝાઇન)", num_questions=10):
    """
    Generate bilingual GSSSB MCQs using Google Gemini API or OpenAI API cleanly.
    Safely handles both google.genai and google.generativeai SDKs.
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
4. Return ONLY valid JSON array.

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
            for m in ['gemini-flash-latest', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        raw_response = resp.text
                        break
                except Exception as err_m:
                    last_err = str(err_m)
        except Exception as e_modern:
            last_err = str(e_modern)

        # 2. Fallback: Legacy google-generativeai SDK (safely handled with try-except)
        if not raw_response:
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                for m_legacy in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
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

    try:
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        clean = match.group(0) if match else raw_response.strip().strip("```json").strip("```").strip()
        parsed = json.loads(clean)
        if isinstance(parsed, list) and len(parsed) > 0:
            return True, parsed
        return False, f"JSON parse error. Snippet: {raw_response[:150]}"
    except Exception as e:
        return False, f"Parsing Exception: {str(e)}"

def generate_bulk_gsssb_mcqs(api_key, text_chunks, subject="Apparel & Fashion Design (ફેશન ડિઝાઇન)", target_total=100, batch_size=20, progress_callback=None):
    """
    Bulk Question Generator looping in batches.
    """
    if not api_key:
        return False, "API Key missing!", []

    if not text_chunks:
        text_chunks = [f"GSSSB Supervisor Instructor exam syllabus for {subject}."]

    total_gen = 0
    all_gen = []
    chunk_idx = 0
    batch_count = 0
    num_chunks = len(text_chunks)

    while total_gen < target_total:
        needed = min(batch_size, target_total - total_gen)
        batch_count += 1
        
        success, result = generate_gsssb_mcqs(api_key, text_chunks[chunk_idx % num_chunks], subject, needed)
        
        if success and isinstance(result, list):
            saved = db.save_new_questions(result, "Question_Bank")
            total_gen += saved
            all_gen.extend(result)
            if progress_callback:
                progress_callback(total_gen, target_total, result, batch_count)
            chunk_idx += 1
            time.sleep(1)
        else:
            if "API Error" in str(result) or "API Key" in str(result):
                return False, f"❌ {result}", all_gen
            time.sleep(2)
            chunk_idx += 1
            if batch_count > (target_total // batch_size) * 3 + 5:
                return False, f"❌ Generation halted: {result}", all_gen

    return True, f"Successfully generated and saved {total_gen} MCQs in {batch_count} batches!", all_gen
