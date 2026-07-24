import json
import os
import pandas as pd
from database import init_db, save_new_questions, EXCEL_FILE

INITIAL_QUESTIONS = [
    # ---------------- Apparel & Fashion Design ----------------
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "ગાર્મેન્ટ કન્સ્ટ્રક્શનમાં કપડાની કિનારીને ફાટતી અટકાવવા કઈ સિલાઈ (Stitch) નો ઉપયોગ થાય છે?",
        "Options_GU": ["A) ઓવરલોક સિલાઈ (Overlock Stitch)", "B) રનિંગ સિલાઈ (Running Stitch)", "C) બેક સિલાઈ (Back Stitch)", "D) બાસ્ટિંગ સિલાઈ (Basting Stitch)"],
        "Question_EN": "Which stitch is commonly used in garment construction to prevent edge fraying?",
        "Options_EN": ["A) Overlock Stitch", "B) Running Stitch", "C) Back Stitch", "D) Basting Stitch"],
        "Correct_Answer": "A",
        "Difficulty": "Medium"
    },
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "ટેક્સટાઇલ ફાઇબરમાં 'કોટન' (Cotton) કયા પ્રકારનું ફાઇબર ગણાય છે?",
        "Options_GU": ["A) કુદરતી સેલ્યુલોઝિક ફાઇબર (Natural Cellulosic)", "B) કૃત્રિમ સિન્થેટિક ફાઇબર (Synthetic Polymer)", "C) પ્રાણીજન્ય પ્રોટીન ફાઇબર (Animal Protein)", "D) મિનરલ ફાઇબર (Mineral Fiber)"],
        "Question_EN": "What category of fiber does 'Cotton' belong to in textile science?",
        "Options_EN": ["A) Natural Cellulosic Fiber", "B) Synthetic Polymer Fiber", "C) Animal Protein Fiber", "D) Mineral Fiber"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "પેટર્ન મેકિંગમાં 'ડાર્ટ' (Dart) નો મુખ્ય હેતુ શું છે?",
        "Options_GU": ["A) કાપડને ૩D શારીરિક આકાર અને ફિટિંગ આપવું", "B) કાપડની મજબૂતી વધારવી", "C) માત્ર સુશોભન (Decoration) માટે", "D) બટન લગાવવા માટે"],
        "Question_EN": "What is the primary purpose of a 'Dart' in pattern drafting?",
        "Options_EN": ["A) To provide 3D body shaping and proper fitting", "B) To increase fabric tensile strength", "C) For decorative embellishment only", "D) For button attachment"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "ફેશન સાયકલ (Fashion Cycle) નું પ્રથમ તબક્કો કયો છે?",
        "Options_GU": ["A) ઇન્ટ્રોડક્શન (Introduction)", "B) રાઇઝ (Rise)", "C) પีก (Peak)", "D) ઓબ્સોલેસન્સ (Obsolescence)"],
        "Question_EN": "What is the initial stage of the Fashion Cycle?",
        "Options_EN": ["A) Introduction", "B) Rise", "C) Peak", "D) Obsolescence"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "સિલિંગ અને ગાર્મેન્ટ ડિઝાઇનિંગ માટે કયા કમ્પ્યુટર સોફ્ટવેર (CAD) નો ઉપયોગ થાય છે?",
        "Options_GU": ["A) Lectra / Gerber / Optitex", "B) MS PowerPoint", "C) Tally Prime", "D) AutoCAD Civil"],
        "Question_EN": "Which Computer-Aided Design (CAD) software is widely used in apparel pattern making & grading?",
        "Options_EN": ["A) Lectra / Gerber / Optitex", "B) MS PowerPoint", "C) Tally Prime", "D) AutoCAD Civil"],
        "Correct_Answer": "A",
        "Difficulty": "Medium"
    },
    {
        "Subject": "Apparel & Fashion Design (ફેશન ડિઝાઇન)",
        "Question_GU": "ગુજરાતની કઈ પરંપરાગત ભરતકામ શૈલી અરીસા (Mirror work) અને રેશમના ધાગા માટે પ્રખ્યાત છે?",
        "Options_GU": ["A) કચ્છી ભરતકામ (Kutchi Embroidery)", "B) ચિકનકારી (Chikan work)", "C) ઝરદોઝી (Zardozi)", "D) કાંથા (Kantha)"],
        "Question_EN": "Which traditional embroidery style of Gujarat is famous for mirror work and vibrant silk thread stitch?",
        "Options_EN": ["A) Kutchi Embroidery", "B) Chikan work", "C) Zardozi", "D) Kantha"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },

    # ---------------- Mathematics ----------------
    {
        "Subject": "Mathematics (ગણિત)",
        "Question_GU": "જો એક વસ્તુ ₹ ૮૦૦ માં ખરીદીને ₹ ૧૦૦૦ માં વેચવામાં આવે, તો નફાની ટકાવારી કેટલી થાય?",
        "Options_GU": ["A) ૨૫%", "B) ૨૦%", "C) ૧૫%", "D) ૩૦%"],
        "Question_EN": "If an item purchased for ₹800 is sold for ₹1000, what is the profit percentage?",
        "Options_EN": ["A) 25%", "B) 20%", "C) 15%", "D) 30%"],
        "Correct_Answer": "A",
        "Difficulty": "Medium"
    },
    {
        "Subject": "Mathematics (ગણિત)",
        "Question_GU": "પ્રથમ ૧૦ નૈસર્ગિક સંખ્યાઓ (Natural Numbers) ની સરેરાશ કેટલી થાય?",
        "Options_GU": ["A) ૫.૫", "B) ૫.૦", "C) ૬.૦", "D) ૬.૫"],
        "Question_EN": "What is the average of the first 10 natural numbers?",
        "Options_EN": ["A) 5.5", "B) 5.0", "C) 6.0", "D) 6.5"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },

    # ---------------- Reasoning ----------------
    {
        "Subject": "Reasoning (રિઝનિંગ)",
        "Question_GU": "શ્રેણી પૂર્ણ કરો: ૨, ૪, ૮, ૧૬, ૩૨, ?",
        "Options_GU": ["A) ૬૪", "B) ૪૮", "C) ૫૦", "D) ૭૨"],
        "Question_EN": "Complete the series: 2, 4, 8, 16, 32, ?",
        "Options_EN": ["A) 64", "B) 48", "C) 50", "D) 72"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },
    {
        "Subject": "Reasoning (રિઝનિંગ)",
        "Question_GU": "જો CLOTH નો કોડ DNPUI હોય, તો DRESS નો કોડ શું થાય?",
        "Options_GU": ["A) ESFTT", "B) ERFSS", "C) EQDRR", "D) FSGUU"],
        "Question_EN": "If CLOTH is coded as DNPUI, what will be the code for DRESS (+1 logic)?",
        "Options_EN": ["A) ESFTT", "B) ERFSS", "C) EQDRR", "D) FSGUU"],
        "Correct_Answer": "A",
        "Difficulty": "Medium"
    },

    # ---------------- Gujarati Grammar ----------------
    {
        "Subject": "Gujarati Grammar (ગુજરાતી વ્યાકરણ)",
        "Question_GU": "'સૂર્યોદય' શબ્દની સાચી સંધિ છોડો.",
        "Options_GU": ["A) સૂર્ય + ઉદય", "B) સૂર્ય + ઉદયી", "C) સૂર્યો + દય", "D) સુરી + ઉદય"],
        "Question_EN": "Identify the correct Sandhi split for the word 'Suryoday' in Gujarati grammar.",
        "Options_EN": ["A) Surya + Uday", "B) Surya + Udayi", "C) Suryo + Day", "D) Suri + Uday"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },
    {
        "Subject": "Gujarati Grammar (ગુજરાતી વ્યાકરણ)",
        "Question_GU": "'હાથ ચાલાક હોવું' રૂઢિપ્રયોગનો સાચો અર્થ જણાવો.",
        "Options_GU": ["A) ચોરી કરવાની ટેવ હોવી / કામમાં ઝડપ હોવી", "B) હાથ સુંદર હોવા", "C) મહેનત કરવી", "D) દાન આપવું"],
        "Question_EN": "What is the meaning of the Gujarati idiom 'Hath chalak hovu'?",
        "Options_EN": ["A) Quickness in work / skillfulness", "B) Having beautiful hands", "C) Working hard", "D) Donating money"],
        "Correct_Answer": "A",
        "Difficulty": "Medium"
    },

    # ---------------- English Grammar ----------------
    {
        "Subject": "English Grammar (ઇંગ્લિશ વ્યાકરણ)",
        "Question_GU": "સંપૂર્ણ વાક્ય પસંદ કરો: She ______ to the market yesterday.",
        "Options_GU": ["A) went", "B) go", "C) goes", "D) gone"],
        "Question_EN": "Choose the correct past tense verb: She ______ to the market yesterday.",
        "Options_EN": ["A) went", "B) go", "C) goes", "D) gone"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    },

    # ---------------- Current Affairs ----------------
    {
        "Subject": "Current Affairs (ચાલુ વર્તમાન પ્રવાહો)",
        "Question_GU": "ગુજરાતના કયા શહેરમાં ગિફ્ટ સિટી (GIFT City) આવેલું છે?",
        "Options_GU": ["A) ગાંધીનગર", "B) અહમદાબાદ", "C) સુરત", "D) વડોદરા"],
        "Question_EN": "In which city of Gujarat is GIFT City (Gujarat International Finance Tec-City) located?",
        "Options_EN": ["A) Gandhinagar", "B) Ahmedabad", "C) Surat", "D) Vadodara"],
        "Correct_Answer": "A",
        "Difficulty": "Easy"
    }
]

def seed_database():
    init_db(EXCEL_FILE)
    count = save_new_questions(INITIAL_QUESTIONS, sheet_name="Question_Bank", excel_path=EXCEL_FILE)
    print(f"Successfully seeded database with {count} GSSSB MCQs into gsssb_question_bank.xlsx")

if __name__ == "__main__":
    seed_database()

