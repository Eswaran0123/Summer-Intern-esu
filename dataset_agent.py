import os
import time

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from dataset_tools import (
    dataset_overview,
    column_statistics,
    top_students,
    weak_students,
    subject_performance,
    find_student
)


# ==========================================================
# LOAD API KEY
# ==========================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is missing. "
        "Please add GOOGLE_API_KEY to .env"
    )


# ==========================================================
# SYSTEM PROMPT
# ==========================================================

SYSTEM_PROMPT = """
You are an intelligent Dataset Analysis Agent.

You analyze CSV and Excel datasets uploaded by the user.

RULES:

1. Always use the available tools when dataset information is required.
2. Never invent values.
3. Never assume fixed column names.
4. Use the uploaded dataset as the source of truth.
5. Give clear and simple answers.
6. If a requested column does not exist, explain the available columns.
7. For student questions, use the student search tool.
8. For numerical questions, use the appropriate analysis tool.

You can answer questions such as:

- Show dataset overview.
- What is the average maths mark?
- What is the average science mark?
- Find the top 5 students in maths.
- Find students below 40 in maths.
- Which subject has the highest average?
- Find a particular student.
- Show statistics for a column.
- Compare subject performance.

Do not invent data.
"""


# ==========================================================
# AVAILABLE GEMINI MODELS
# ==========================================================

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]


# ==========================================================
# CREATE AGENT
# ==========================================================

def create_dataset_agent(model_name):

    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=GOOGLE_API_KEY,
        timeout=30,
        max_retries=0
    )

    agent = create_agent(
        model=model,
        tools=[
            dataset_overview,
            column_statistics,
            top_students,
            weak_students,
            subject_performance,
            find_student
        ],
        system_prompt=SYSTEM_PROMPT
    )

    return agent


# ==========================================================
# CHECK WHETHER ERROR IS TEMPORARY
# ==========================================================

def is_retryable_error(error):

    error_text = str(error).upper()

    retryable_errors = [
        "503",
        "UNAVAILABLE",
        "429",
        "RESOURCE_EXHAUSTED",
        "500",
        "INTERNAL",
        "TIMEOUT",
        "DEADLINE",
        "CONNECTION",
        "10053"
    ]

    return any(
        item in error_text
        for item in retryable_errors
    )


# ==========================================================
# EXTRACT FINAL RESPONSE
# ==========================================================

def extract_response(response):

    messages = response.get("messages", [])

    if not messages:
        return "No response generated."

    # Find the last AI message
    for message in reversed(messages):

        content = getattr(
            message,
            "content",
            None
        )

        if not content:
            continue

        if isinstance(content, str):
            return content

        if isinstance(content, list):

            text_parts = []

            for item in content:

                if isinstance(item, dict):

                    if item.get("type") == "text":
                        text_parts.append(
                            item.get("text", "")
                        )

                elif isinstance(item, str):
                    text_parts.append(item)

            if text_parts:
                return "\n".join(text_parts)

    return str(messages[-1].content)


# ==========================================================
# RUN DATASET AGENT
# ==========================================================

def run_dataset_agent(question):

    last_error = None

    for model_name in MODELS:

        try:

            print(
                f"🤖 Trying Gemini model: {model_name}"
            )

            agent = create_dataset_agent(
                model_name
            )

            response = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
                }
            )

            answer = extract_response(response)

            print(
                f"✅ Successfully used: {model_name}"
            )

            return answer

        except Exception as error:

            last_error = error

            print(
                f"⚠️ {model_name} failed:"
            )

            print(error)

            if is_retryable_error(error):

                print(
                    f"🔄 Trying next model..."
                )

                time.sleep(2)

                continue

            else:

                return (
                    "❌ Dataset Agent Error:\n\n"
                    f"{error}"
                )

    # ======================================================
    # ALL MODELS FAILED
    # ======================================================

    return (
        "❌ Gemini is currently unavailable.\n\n"
        "I tried multiple Gemini models, but "
        "all requests failed.\n\n"
        f"Last error:\n{last_error}\n\n"
        "Please wait a little and try again."
    )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("================================")
    print("DATASET AGENT READY")
    print("================================")

    print(
        "Available models:"
    )

    for model in MODELS:
        print(
            f" - {model}"
        )