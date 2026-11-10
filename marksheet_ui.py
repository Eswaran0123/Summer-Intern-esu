# ==========================================================
# AI MARKSHEET ANALYZER + CHAT AGENT
# ==========================================================

import streamlit as st

from marksheet_agent import extract_marksheet
from marksheet_chat_agent import ask_marksheet_agent


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Marksheet AI",
    page_icon="📄",
    layout="wide"
)


# ==========================================================
# SESSION STATE
# ==========================================================

if "marksheet_data" not in st.session_state:
    st.session_state.marksheet_data = None

if "marksheet_chat" not in st.session_state:
    st.session_state.marksheet_chat = []

if "marksheet_filename" not in st.session_state:
    st.session_state.marksheet_filename = None


# ==========================================================
# TITLE
# ==========================================================

st.title("📄 AI Marksheet Analyzer")

st.write(
    "Upload your 10th, 12th or College marksheet "
    "and interact with the Marksheet AI Agent."
)


# ==========================================================
# UPLOAD
# ==========================================================

uploaded_file = st.file_uploader(
    "📤 Upload Marksheet",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


# ==========================================================
# PROCESS IMAGE
# ==========================================================

if uploaded_file is not None:

    # Process only when a new file is uploaded

    if (
        st.session_state.marksheet_filename
        != uploaded_file.name
    ):

        with st.spinner(
            "🤖 Gemini Vision is analyzing the marksheet..."
        ):

            image_bytes = uploaded_file.getvalue()

            result = extract_marksheet(
                image_bytes,
                uploaded_file.type
            )


        # --------------------------------------------------
        # ERROR
        # --------------------------------------------------

        if "error" in result:

            st.error(
                f"❌ {result.get('error')}"
            )

            st.write(
                "**Error Type:**",
                result.get(
                    "error_type",
                    "Unknown"
                )
            )

            if result.get("details"):

                st.code(
                    result["details"]
                )

        else:

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            st.session_state.marksheet_data = result

            st.session_state.marksheet_filename = (
                uploaded_file.name
            )

            # New marksheet = new chat
            st.session_state.marksheet_chat = []

            st.success(
                "✅ Marksheet analyzed successfully!"
            )


# ==========================================================
# CHECK MARKSHEET
# ==========================================================

if st.session_state.marksheet_data is None:

    st.info(
        "👆 Upload a marksheet to start."
    )

    st.stop()


result = st.session_state.marksheet_data


# ==========================================================
# STUDENT DETAILS
# ==========================================================

st.subheader("👤 Student Details")

col1, col2 = st.columns(2)

with col1:

    st.write(
        "**Student Name:**",
        result.get("student_name") or "-"
    )

    st.write(
        "**Register Number:**",
        result.get("register_number") or "-"
    )

    st.write(
        "**Marksheet Type:**",
        result.get("marksheet_type") or "-"
    )


with col2:

    st.write(
        "**School / College:**",
        result.get("school_or_college") or "-"
    )

    st.write(
        "**Exam Year:**",
        result.get("exam_year") or "-"
    )

    st.write(
        "**Semester:**",
        result.get("semester") or "-"
    )


# ==========================================================
# SUBJECT DETAILS
# ==========================================================

subjects = result.get(
    "subjects",
    []
)


if subjects:

    st.subheader("📚 Subject Details")

    st.dataframe(
        subjects,
        use_container_width=True
    )


# ==========================================================
# MARKS SUMMARY
# ==========================================================

st.subheader("📊 Marks Summary")

total_marks = result.get(
    "total_marks"
)

maximum_marks = result.get(
    "maximum_total_marks"
)


# Calculate percentage if Gemini didn't provide it

percentage = result.get(
    "percentage"
)

if (
    percentage is None
    and total_marks is not None
    and maximum_marks is not None
):

    try:

        percentage = round(
            (
                float(total_marks)
                / float(maximum_marks)
            ) * 100,
            2
        )

        # Save calculated percentage

        result["percentage"] = percentage

    except Exception:
        percentage = None


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Marks",
        total_marks or "-"
    )


with col2:

    st.metric(
        "Maximum Marks",
        maximum_marks or "-"
    )


with col3:

    if percentage is not None:

        st.metric(
            "Percentage",
            f"{percentage}%"
        )

    else:

        st.metric(
            "Percentage",
            "-"
        )


# ==========================================================
# AI MARKSHEET CHAT
# ==========================================================

st.divider()

st.subheader("🤖 Ask Marksheet AI")

st.write(
    "Ask questions about this student's marksheet."
)


# ==========================================================
# SHOW CHAT HISTORY
# ==========================================================

for message in st.session_state.marksheet_chat:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ==========================================================
# CHAT INPUT
# ==========================================================

question = st.chat_input(
    "Example: What is my percentage?"
)


# ==========================================================
# PROCESS QUESTION
# ==========================================================

if question:

    # ------------------------------------------------------
    # USER MESSAGE
    # ------------------------------------------------------

    st.session_state.marksheet_chat.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    # ------------------------------------------------------
    # AI RESPONSE
    # ------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "🤖 Marksheet Agent is thinking..."
        ):

            answer = ask_marksheet_agent(

                question=question,

                marksheet_data=result,

                chat_history=st.session_state.marksheet_chat
            )


        st.markdown(answer)


    # ------------------------------------------------------
    # SAVE RESPONSE
    # ------------------------------------------------------

    st.session_state.marksheet_chat.append(
        {
            "role": "assistant",
            "content": answer
        }
    )