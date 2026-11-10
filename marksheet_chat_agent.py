# ==========================================================
# MARKSHEET CHAT AGENT
# ==========================================================

import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in .env")

client = genai.Client(
    api_key=GOOGLE_API_KEY
)


# ==========================================================
# SYSTEM PROMPT
# ==========================================================

SYSTEM_PROMPT = """
You are a Marksheet AI Assistant.

You answer questions about the student's uploaded marksheet.

IMPORTANT RULES:

1. Use ONLY the marksheet data provided to you.
2. Never invent marks or student information.
3. If information is not available, clearly say:
   "This information is not available in the extracted marksheet."
4. Answer in simple language.
5. For numerical questions, calculate carefully.
6. You can calculate:
   - Total marks
   - Percentage
   - Highest mark
   - Lowest mark
   - Average mark
   - Subject comparison
7. For 10th and 12th marksheets, explain percentage clearly.
8. For college marksheets, explain grades, grade points,
   credits, SGPA and CGPA only when sufficient data exists.
9. Do not claim an official SGPA/CGPA if the required
   credit or grade information is missing.
10. If the user asks about a subject, use the exact
    extracted subject information.

You are a helpful academic assistant.
"""


# ==========================================================
# ASK MARKSHEET AGENT
# ==========================================================

def ask_marksheet_agent(
    question,
    marksheet_data,
    chat_history=None
):

    if chat_history is None:
        chat_history = []


    # ------------------------------------------------------
    # CREATE MARKSHEET CONTEXT
    # ------------------------------------------------------

    marksheet_context = json.dumps(
        marksheet_data,
        indent=2,
        ensure_ascii=False
    )


    # ------------------------------------------------------
    # BUILD PROMPT
    # ------------------------------------------------------

    prompt = f"""
{SYSTEM_PROMPT}

==================================================
UPLOADED MARKSHEET DATA
==================================================

{marksheet_context}

==================================================
CONVERSATION HISTORY
==================================================

{json.dumps(chat_history, indent=2, ensure_ascii=False)}

==================================================
CURRENT USER QUESTION
==================================================

{question}

Answer the user's question using the marksheet data.
"""


    # ------------------------------------------------------
    # CALL GEMINI
    # ------------------------------------------------------

    try:

        response = client.models.generate_content(

            model="gemini-3.7-flash",

            contents=prompt
        )

        if response is None:

            return "❌ Gemini returned no response."

        answer = response.text

        if not answer:

            return "❌ Gemini returned an empty response."

        return answer


    except Exception as error:

        error_text = str(error)

        if "429" in error_text:

            return (
                "⚠️ Gemini quota has been exceeded. "
                "Please wait for the quota reset and try again."
            )

        if "503" in error_text:

            return (
                "⚠️ Gemini is temporarily unavailable. "
                "Please try again after a short wait."
            )

        if "504" in error_text:

            return (
                "⚠️ Gemini request timed out. "
                "Please try again."
            )

        return (
            "❌ Marksheet AI Agent Error:\n\n"
            + error_text
        )