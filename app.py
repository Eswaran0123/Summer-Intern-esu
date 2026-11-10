# ==========================================================
# UNIVERSAL ACADEMIC AI
# Dataset + Marksheet + AI Assistant
# ==========================================================

import streamlit as st
import pandas as pd

import data_analyzer

from dataset_agent import run_dataset_agent

from marksheet_agent import extract_marksheet
from marksheet_chat_agent import ask_marksheet_agent


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Universal Data Analysis and Task Automation",
    page_icon="🎓",
    layout="wide"
)


# ==========================================================
# SESSION STATE
# ==========================================================

# Dataset
if "dataset" not in st.session_state:
    st.session_state.dataset = None

if "dataset_filename" not in st.session_state:
    st.session_state.dataset_filename = None

if "dataset_chat" not in st.session_state:
    st.session_state.dataset_chat = []


# Marksheet
if "marksheet_data" not in st.session_state:
    st.session_state.marksheet_data = None

if "marksheet_filename" not in st.session_state:
    st.session_state.marksheet_filename = None

if "marksheet_chat" not in st.session_state:
    st.session_state.marksheet_chat = []


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.title("🎓 Universal Data Analysis and Task Automation")

    st.divider()

    mode = st.radio(
        "Select Module",
        [
            "📊 Dataset Analysis",
            "📄 Marksheet Analysis",
            "🤖 AI Assistant"
        ]
    )

    st.divider()

    st.subheader("⚙️ System")

    st.write("**AI:** Google Gemini")
    st.write("**Framework:** LangChain")
    st.write("**Data:** Pandas")
    st.write("**UI:** Streamlit")
    st.write("**Vision:** Gemini Vision")


# ==========================================================
# HEADER
# ==========================================================

st.title("🎓 Universal Data Analysis and Task Automation")

st.caption(
    "Agentic AI-Based Data Analysis & Task Automation System"
)


# ==========================================================
# DATASET ANALYSIS
# ==========================================================

if mode == "📊 Dataset Analysis":

    st.header("📊 Dataset Analysis")

    st.write(
        "Upload a CSV or Excel dataset and ask questions "
        "using the Dataset AI Agent."
    )


    # ------------------------------------------------------
    # UPLOAD DATASET
    # ------------------------------------------------------

    uploaded_file = st.file_uploader(
        "📂 Upload Student Dataset",
        type=[
            "csv",
            "xlsx",
            "xls"
        ],
        key="dataset_uploader"
    )


    # ------------------------------------------------------
    # READ DATASET
    # ------------------------------------------------------

    if uploaded_file is not None:

        if (
            st.session_state.dataset_filename
            != uploaded_file.name
        ):

            try:

                if uploaded_file.name.lower().endswith(
                    ".csv"
                ):

                    df = pd.read_csv(
                        uploaded_file
                    )

                else:

                    df = pd.read_excel(
                        uploaded_file
                    )


                st.session_state.dataset = df.copy()

                st.session_state.dataset_filename = (
                    uploaded_file.name
                )

                # Store for Dataset Agent
                data_analyzer.set_data(
                    df,
                    uploaded_file.name
                )

                # Reset dataset chat for new file
                st.session_state.dataset_chat = []

                st.success(
                    f"✅ {uploaded_file.name} uploaded successfully!"
                )


            except Exception as error:

                st.error(
                    f"❌ Error reading dataset: {error}"
                )


    else:

        # Restore existing dataset
        if st.session_state.dataset is not None:

            data_analyzer.set_data(
                st.session_state.dataset,
                st.session_state.dataset_filename
            )


    # ------------------------------------------------------
    # CHECK DATASET
    # ------------------------------------------------------

    if st.session_state.dataset is None:

        st.info(
            "👈 Upload a CSV or Excel dataset to begin."
        )

        st.stop()


    df = st.session_state.dataset


    # ------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------

    st.subheader("📊 Dataset Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Records",
            len(df)
        )

    with col2:

        st.metric(
            "Total Columns",
            len(df.columns)
        )

    with col3:

        st.metric(
            "Missing Values",
            int(
                df.isnull().sum().sum()
            )
        )


    # ------------------------------------------------------
    # DATASET PREVIEW
    # ------------------------------------------------------

    st.subheader("👀 Dataset Preview")

    st.dataframe(
        df,
        use_container_width=True,
        height=350
    )


    # ------------------------------------------------------
    # CHARTS
    # ------------------------------------------------------

    st.subheader("📈 Data Visualization")

    numeric_columns = list(
        df.select_dtypes(
            include="number"
        ).columns
    )


    if numeric_columns:

        selected_column = st.selectbox(
            "Select Numeric Column",
            numeric_columns,
            key="dataset_chart_column"
        )


        chart_type = st.radio(
            "Chart Type",
            [
                "Bar Chart",
                "Line Chart"
            ],
            horizontal=True,
            key="dataset_chart_type"
        )


        chart_data = df[
            [selected_column]
        ]


        if chart_type == "Bar Chart":

            st.bar_chart(
                chart_data
            )

        else:

            st.line_chart(
                chart_data
            )

    else:

        st.warning(
            "No numeric columns available."
        )


    # ------------------------------------------------------
    # DATASET CHAT
    # ------------------------------------------------------

    st.divider()

    st.subheader("🤖 Ask Dataset AI")

    st.write(
        "Ask questions about your uploaded dataset."
    )


    # Show previous messages

    for message in st.session_state.dataset_chat:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    question = st.chat_input(
        "Example: Find the top 5 students in maths",
        key="dataset_chat_input"
    )


    if question:

        # User message
        st.session_state.dataset_chat.append(
            {
                "role": "user",
                "content": question
            }
        )


        with st.chat_message("user"):

            st.markdown(
                question
            )


        # Agent
        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Dataset Agent is analyzing..."
            ):

                answer = run_dataset_agent(
                    question
                )


            st.markdown(
                answer
            )


        # Save response
        st.session_state.dataset_chat.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# ==========================================================
# MARKSHEET ANALYSIS
# ==========================================================

elif mode == "📄 Marksheet Analysis":

    st.header("📄 AI Marksheet Analyzer")

    st.write(
        "Upload your 10th, 12th or College marksheet "
        "and interact with the Marksheet AI Agent."
    )


    # ------------------------------------------------------
    # UPLOAD MARKSHEET
    # ------------------------------------------------------

    uploaded_file = st.file_uploader(
        "📤 Upload Marksheet",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ],
        key="marksheet_uploader"
    )


    # ------------------------------------------------------
    # PROCESS MARKSHEET
    # ------------------------------------------------------

    if uploaded_file is not None:

        if (
            st.session_state.marksheet_filename
            != uploaded_file.name
        ):

            with st.spinner(
                "🤖 Gemini Vision is analyzing the marksheet..."
            ):

                image_bytes = (
                    uploaded_file.getvalue()
                )

                result = extract_marksheet(
                    image_bytes,
                    uploaded_file.type
                )


            # ------------------------------------------------
            # ERROR
            # ------------------------------------------------

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


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            else:

                st.session_state.marksheet_data = (
                    result
                )

                st.session_state.marksheet_filename = (
                    uploaded_file.name
                )

                st.session_state.marksheet_chat = []

                st.success(
                    "✅ Marksheet analyzed successfully!"
                )


    # ------------------------------------------------------
    # CHECK MARKSHEET
    # ------------------------------------------------------

    if st.session_state.marksheet_data is None:

        st.info(
            "👆 Upload a marksheet to begin."
        )

        st.stop()


    result = st.session_state.marksheet_data


    # ------------------------------------------------------
    # STUDENT DETAILS
    # ------------------------------------------------------

    st.subheader("👤 Student Details")

    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**Student Name:**",
            result.get(
                "student_name"
            ) or "-"
        )

        st.write(
            "**Register Number:**",
            result.get(
                "register_number"
            ) or "-"
        )

        st.write(
            "**Marksheet Type:**",
            result.get(
                "marksheet_type"
            ) or "-"
        )


    with col2:

        st.write(
            "**School / College:**",
            result.get(
                "school_or_college"
            ) or "-"
        )

        st.write(
            "**Exam Year:**",
            result.get(
                "exam_year"
            ) or "-"
        )

        st.write(
            "**Semester:**",
            result.get(
                "semester"
            ) or "-"
        )


    # ------------------------------------------------------
    # SUBJECTS
    # ------------------------------------------------------

    subjects = result.get(
        "subjects",
        []
    )


    if subjects:

        st.subheader(
            "📚 Subject Details"
        )

        st.dataframe(
            subjects,
            use_container_width=True
        )


    # ------------------------------------------------------
    # MARKS SUMMARY
    # ------------------------------------------------------

    st.subheader(
        "📊 Marks Summary"
    )


    total_marks = result.get(
        "total_marks"
    )

    maximum_marks = result.get(
        "maximum_total_marks"
    )

    percentage = result.get(
        "percentage"
    )


    # Calculate percentage if needed

    if (
        percentage is None
        and total_marks is not None
        and maximum_marks is not None
    ):

        try:

            percentage = round(
                (
                    float(total_marks)
                    /
                    float(maximum_marks)
                ) * 100,
                2
            )

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


    # ------------------------------------------------------
    # MARKSHEET CHAT
    # ------------------------------------------------------

    st.divider()

    st.subheader(
        "🤖 Ask Marksheet AI"
    )

    st.write(
        "Ask questions about this student's marksheet."
    )


    # Show chat history

    for message in st.session_state.marksheet_chat:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    question = st.chat_input(
        "Example: What is my percentage?",
        key="marksheet_chat_input"
    )


    if question:

        # User
        st.session_state.marksheet_chat.append(
            {
                "role": "user",
                "content": question
            }
        )


        with st.chat_message("user"):

            st.markdown(
                question
            )


        # AI
        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Marksheet Agent is thinking..."
            ):

                answer = ask_marksheet_agent(
                    question=question,
                    marksheet_data=result,
                    chat_history=st.session_state.marksheet_chat
                )


            st.markdown(
                answer
            )


        # Save
        st.session_state.marksheet_chat.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# ==========================================================
# AI ASSISTANT
# ==========================================================

elif mode == "🤖 AI Assistant":

    st.header("🤖 Academic AI Assistant")

    st.write(
        "Your intelligent assistant for academic "
        "datasets and marksheets."
    )


    st.info(
        "🚀 Central AI Assistant will connect the "
        "Dataset Agent and Marksheet Agent."
    )


    st.subheader(
        "🧠 Available AI Agents"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.success(
            "📊 Dataset Analysis Agent"
        )

        st.write(
            "Analyzes CSV and Excel academic datasets."
        )


    with col2:

        st.success(
            "📄 Marksheet Analysis Agent"
        )

        st.write(
            "Analyzes 10th, 12th and college marksheets."
        )


    st.divider()


    st.subheader(
        "🔀 Agentic AI Architecture"
    )

    st.code(
        """
User
 │
 ▼
AI Assistant / Router Agent
 │
 ├── 📊 Dataset Agent
 │      └── CSV / Excel
 │
 └── 📄 Marksheet Agent
        └── Gemini Vision
        """,
        language="text"
    )


    st.warning(
        "Next step: We will add the Router Agent here "
        "so the user can ask everything from one chat."
    )