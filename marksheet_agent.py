
# ==========================================================
# MARKSHEET AI AGENT
# Local EasyOCR + Gemini Vision Fallback
# Compatible with Universal Academic AI
# ==========================================================

import os
import re
import json
import time
import base64

from io import BytesIO

import numpy as np
import easyocr

from PIL import Image, ImageOps
from dotenv import load_dotenv
from google import genai


# ==========================================================
# LOAD ENVIRONMENT
# ==========================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ==========================================================
# GEMINI CLIENT
# ==========================================================

client = None

if GOOGLE_API_KEY:

    client = genai.Client(
        api_key=GOOGLE_API_KEY,
        http_options={
            "timeout": 300000
        }
    )


# ==========================================================
# EASY OCR CONFIGURATION
# ==========================================================

# Reader is initialized only when required.
# It remains available for subsequent uploads.

ocr_reader = None


def get_ocr_reader():

    global ocr_reader

    if ocr_reader is None:

        print("Loading EasyOCR model...")

        ocr_reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

        print("EasyOCR model loaded successfully.")

    return ocr_reader


# ==========================================================
# GEMINI VISION PROMPT
# ==========================================================

MARKSHEET_PROMPT = """
You are an AI Academic Marksheet Analyzer.

Carefully analyze the uploaded marksheet image.

RULES:

1. Never guess or invent information.
2. Extract only clearly visible information.
3. Use null for missing or unclear values.
4. Identify marksheet type:
   10th, 12th, College, or Unknown.
5. Extract student name, register number,
   school or college, exam year and semester.
6. Extract every visible subject and its:
   marks, maximum marks, grade, grade point and credits.
7. Extract total marks and maximum total marks.
8. Do not invent subject marks.
9. Do not calculate official SGPA or CGPA without
   sufficient credit and grade information.
10. Return ONLY valid JSON.

Use exactly this structure:

{
    "marksheet_type": null,
    "student_name": null,
    "register_number": null,
    "school_or_college": null,
    "exam_year": null,
    "semester": null,
    "subjects": [
        {
            "subject": null,
            "marks": null,
            "max_marks": null,
            "grade": null,
            "grade_point": null,
            "credits": null
        }
    ],
    "total_marks": null,
    "maximum_total_marks": null,
    "percentage": null,
    "remarks": null
}
"""


# ==========================================================
# IMAGE OPTIMIZATION
# ==========================================================

def optimize_image(image_bytes):

    image = Image.open(
        BytesIO(image_bytes)
    )

    # Correct mobile camera orientation
    image = ImageOps.exif_transpose(image)

    image = image.convert("RGB")

    # Keep enough resolution for marksheet text
    image.thumbnail(
        (1600, 1600),
        Image.Resampling.LANCZOS
    )

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True
    )

    return output.getvalue()


# ==========================================================
# IMAGE TO NUMPY ARRAY
# ==========================================================

def prepare_image(image_bytes):

    image = Image.open(
        BytesIO(image_bytes)
    )

    image = ImageOps.exif_transpose(image)

    image = image.convert("RGB")

    image.thumbnail(
        (1600, 1600),
        Image.Resampling.LANCZOS
    )

    return np.array(image)


# ==========================================================
# LOCAL OCR EXTRACTION
# ==========================================================

def extract_text_locally(image_bytes):

    reader = get_ocr_reader()

    image_array = prepare_image(
        image_bytes
    )

    results = reader.readtext(
        image_array,
        detail=1,
        paragraph=False
    )

    extracted_lines = []

    confidences = []

    for item in results:

        if len(item) < 3:
            continue

        text = str(item[1]).strip()

        confidence = float(item[2])

        if text:

            extracted_lines.append(text)

            confidences.append(confidence)

    if confidences:

        average_confidence = (
            sum(confidences) / len(confidences)
        )

    else:

        average_confidence = 0

    return {
        "lines": extracted_lines,
        "average_confidence": average_confidence
    }


# ==========================================================
# HELPER: EXTRACT VALUE AFTER LABEL
# ==========================================================

def extract_labeled_value(lines, labels):

    for line in lines:

        clean_line = line.strip()

        for label in labels:

            pattern = (
                r"^\s*"
                + re.escape(label)
                + r"\s*[:\-]?\s*(.+)$"
            )

            match = re.search(
                pattern,
                clean_line,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                if value:

                    return value

    return None


# ==========================================================
# HELPER: NORMALIZE NUMBERS
# ==========================================================

def extract_numbers(line):

    return re.findall(
        r"\d+(?:\.\d+)?",
        line
    )


def number_or_none(value):

    if value is None:
        return None

    try:

        number = float(value)

        if number.is_integer():

            return int(number)

        return number

    except (ValueError, TypeError):

        return None


# ==========================================================
# IDENTIFY MARKSHEET TYPE
# ==========================================================

def identify_marksheet_type(text):

    text = text.lower()

    if (
        "higher secondary" in text
        or "hsc" in text
        or "class xii" in text
        or "class 12" in text
        or "12th standard" in text
        or "plus two" in text
    ):

        return "12th"

    if (
        "sslc" in text
        or "class x" in text
        or "class 10" in text
        or "10th standard" in text
    ):

        return "10th"

    if (
        "semester" in text
        or "sgpa" in text
        or "cgpa" in text
        or "university examination" in text
    ):

        return "College"

    return "Unknown"


# ==========================================================
# EXTRACT SUBJECT MARKS FROM OCR TEXT
# ==========================================================

def extract_subjects(lines):

    subjects = []

    excluded_words = [
        "total",
        "grand total",
        "maximum",
        "minimum",
        "register",
        "registration",
        "hall ticket",
        "date of birth",
        "percentage",
        "result",
        "grade",
        "marks obtained",
        "subject code",
        "certificate",
        "signature",
        "candidate",
        "name",
        "number"
    ]

    for line in lines:

        clean_line = line.strip()

        lower_line = clean_line.lower()

        # Ignore irrelevant lines
        if any(
            word in lower_line
            for word in excluded_words
        ):

            continue

        numbers = extract_numbers(
            clean_line
        )

        # Need at least marks and maximum marks
        if len(numbers) < 2:
            continue

        # Use the last two numeric values
        marks = number_or_none(
            numbers[-2]
        )

        maximum = number_or_none(
            numbers[-1]
        )

        if marks is None or maximum is None:
            continue

        # Validate possible mark values
        if maximum <= 0 or maximum > 1000:
            continue

        if marks < 0 or marks > maximum:
            continue

        # Remove numbers to obtain subject name
        subject_name = re.sub(
            r"\d+(?:\.\d+)?",
            "",
            clean_line
        )

        subject_name = re.sub(
            r"[^A-Za-z&()/.\- ]",
            " ",
            subject_name
        )

        subject_name = re.sub(
            r"\s+",
            " ",
            subject_name
        ).strip()

        if len(subject_name) < 2:
            continue

        # Avoid duplicates
        already_exists = any(
            subject_name.lower()
            == item["subject"].lower()
            for item in subjects
        )

        if already_exists:
            continue

        subjects.append(
            {
                "subject": subject_name,
                "marks": marks,
                "max_marks": maximum,
                "grade": None,
                "grade_point": None,
                "credits": None
            }
        )

    return subjects


# ==========================================================
# EXTRACT TOTAL MARKS
# ==========================================================

def extract_total_marks(lines):

    total_keywords = [
        "total",
        "grand total",
        "aggregate"
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in total_keywords
        ):

            numbers = extract_numbers(line)

            if len(numbers) >= 2:

                total = number_or_none(
                    numbers[-2]
                )

                maximum = number_or_none(
                    numbers[-1]
                )

                if (
                    total is not None
                    and maximum is not None
                    and maximum > 0
                    and total <= maximum
                ):

                    return total, maximum

    return None, None


# ==========================================================
# LOCAL MARKSHEET DATA EXTRACTION
# ==========================================================

def extract_marksheet_locally(ocr_result):

    lines = ocr_result["lines"]

    full_text = "\n".join(lines)

    lower_text = full_text.lower()

    # Student details
    student_name = extract_labeled_value(
        lines,
        [
            "student name",
            "candidate name",
            "name of the student",
            "name"
        ]
    )

    register_number = extract_labeled_value(
        lines,
        [
            "register number",
            "registration number",
            "reg no",
            "reg. no",
            "roll number",
            "roll no"
        ]
    )

    school_or_college = extract_labeled_value(
        lines,
        [
            "school name",
            "college name",
            "institution name",
            "school",
            "college"
        ]
    )

    # Exam year
    year_match = re.search(
        r"\b(?:19|20)\d{2}\b",
        full_text
    )

    exam_year = (
        int(year_match.group())
        if year_match
        else None
    )

    # Semester
    semester = None

    semester_match = re.search(
        r"\b(?:semester|sem)\s*[-:]?\s*(\d{1,2})\b",
        full_text,
        re.IGNORECASE
    )

    if semester_match:

        semester = semester_match.group(1)

    # Marksheet type
    marksheet_type = identify_marksheet_type(
        full_text
    )

    # Subjects
    subjects = extract_subjects(
        lines
    )

    # Total
    total_marks, maximum_total_marks = (
        extract_total_marks(lines)
    )

    # Calculate percentage only if total is available
    percentage = None

    if (
        total_marks is not None
        and maximum_total_marks is not None
        and maximum_total_marks > 0
    ):

        percentage = round(
            (
                total_marks
                / maximum_total_marks
            ) * 100,
            2
        )

    data = {

        "marksheet_type": marksheet_type,

        "student_name": student_name,

        "register_number": register_number,

        "school_or_college": school_or_college,

        "exam_year": exam_year,

        "semester": semester,

        "subjects": subjects,

        "total_marks": total_marks,

        "maximum_total_marks": maximum_total_marks,

        "percentage": percentage,

        "remarks": "Extracted using local EasyOCR."
    }

    # Confidence indicators
    confidence = ocr_result[
        "average_confidence"
    ]

    has_enough_subjects = len(subjects) >= 2

    has_identification = bool(
        student_name
        or register_number
        or total_marks is not None
    )

    has_academic_type = (
        marksheet_type != "Unknown"
    )

    is_reliable = (
        confidence >= 0.45
        and has_enough_subjects
        and has_identification
        and has_academic_type
    )

    return data, is_reliable


# ==========================================================
# CLEAN GEMINI RESPONSE
# ==========================================================

def clean_json_response(response_text):

    result = response_text.strip()

    if result.startswith("```json"):

        result = result[7:]

    elif result.startswith("```"):

        result = result[3:]

    if result.endswith("```"):

        result = result[:-3]

    return json.loads(
        result.strip()
    )


# ==========================================================
# GEMINI VISION FALLBACK
# ==========================================================

def extract_with_gemini(image_bytes):

    if client is None:

        raise ValueError(
            "GOOGLE_API_KEY is missing. "
            "Cannot use Gemini Vision fallback."
        )

    optimized_image = optimize_image(
        image_bytes
    )

    image_base64 = base64.b64encode(
        optimized_image
    ).decode("utf-8")

    print("Calling Gemini Vision fallback...")

    interaction = client.interactions.create(

        model="gemini-3.7-flash",

        input=[
            {
                "type": "text",
                "text": MARKSHEET_PROMPT
            },
            {
                "type": "image",
                "data": image_base64,
                "mime_type": "image/jpeg"
            }
        ]
    )

    response_text = interaction.output_text

    if not response_text:

        raise ValueError(
            "Gemini returned an empty response."
        )

    data = clean_json_response(
        response_text
    )

    # Preserve the expected structure
    data.setdefault("marksheet_type", None)
    data.setdefault("student_name", None)
    data.setdefault("register_number", None)
    data.setdefault("school_or_college", None)
    data.setdefault("exam_year", None)
    data.setdefault("semester", None)
    data.setdefault("subjects", [])
    data.setdefault("total_marks", None)
    data.setdefault("maximum_total_marks", None)
    data.setdefault("percentage", None)
    data.setdefault("remarks", None)

    if not isinstance(data["subjects"], list):

        data["subjects"] = []

    for subject in data["subjects"]:

        if isinstance(subject, dict):

            subject.setdefault("subject", None)
            subject.setdefault("marks", None)
            subject.setdefault("max_marks", None)
            subject.setdefault("grade", None)
            subject.setdefault("grade_point", None)
            subject.setdefault("credits", None)

    data["remarks"] = (
        "Analyzed using Gemini Vision fallback."
    )

    return data


# ==========================================================
# MAIN EXTRACTION FUNCTION
# Compatible with existing app.py
# ==========================================================

def extract_marksheet(
    image_bytes,
    mime_type="image/jpeg"
):

    total_start = time.perf_counter()

    if not image_bytes:

        return {
            "error": "No image received.",
            "error_type": "InvalidImage"
        }

    print("\n======================================")
    print("MARKSHEET ANALYSIS STARTED")
    print("======================================")

    # ------------------------------------------------------
    # STEP 1: LOCAL OCR
    # ------------------------------------------------------

    try:

        print("STEP 1: Running local EasyOCR...")

        ocr_start = time.perf_counter()

        ocr_result = extract_text_locally(
            image_bytes
        )

        ocr_time = (
            time.perf_counter() - ocr_start
        )

        print(
            "Local OCR time:",
            round(ocr_time, 2),
            "seconds"
        )

        print(
            "OCR confidence:",
            round(
                ocr_result["average_confidence"],
                2
            )
        )

        print(
            "Detected text lines:",
            len(ocr_result["lines"])
        )

    except Exception as error:

        print("Local OCR failed:", error)

        ocr_result = None

    # ------------------------------------------------------
    # STEP 2: LOCAL DATA EXTRACTION
    # ------------------------------------------------------

    if ocr_result is not None:

        try:

            print("STEP 2: Extracting local marksheet data...")

            local_data, is_reliable = (
                extract_marksheet_locally(
                    ocr_result
                )
            )

            if is_reliable:

                total_time = (
                    time.perf_counter() - total_start
                )

                print("\n======================================")
                print("LOCAL OCR SUCCESS")
                print("Gemini Vision was not required.")
                print(
                    "Total time:",
                    round(total_time, 2),
                    "seconds"
                )
                print("======================================\n")

                return local_data

            print(
                "Local OCR result is incomplete."
            )

            print(
                "Switching to Gemini Vision fallback..."
            )

        except Exception as error:

            print(
                "Local extraction failed:",
                error
            )

    else:

        print(
            "OCR unavailable. Switching to Gemini Vision."
        )

    # ------------------------------------------------------
    # STEP 3: GEMINI VISION FALLBACK
    # ------------------------------------------------------

    try:

        print("STEP 3: Gemini Vision fallback...")

        gemini_start = time.perf_counter()

        result = extract_with_gemini(
            image_bytes
        )

        gemini_time = (
            time.perf_counter() - gemini_start
        )

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            "Gemini processing time:",
            round(gemini_time, 2),
            "seconds"
        )

        print(
            "Total processing time:",
            round(total_time, 2),
            "seconds"
        )

        print("MARKSHEET ANALYSIS SUCCESSFUL")

        return result

    except Exception as error:

        error_type = type(error).__name__

        error_text = str(error)

        print("\n======================================")
        print("MARKSHEET ANALYSIS ERROR")
        print("======================================")
        print("Error Type:", error_type)
        print("Error:", error_text)

        # If local OCR produced some information,
        # return it instead of losing all extracted data.

        if ocr_result is not None:

            try:

                local_data, _ = (
                    extract_marksheet_locally(
                        ocr_result
                    )
                )

                local_data["remarks"] = (
                    "Partial local OCR extraction. "
                    "Gemini fallback failed. "
                    + error_text
                )

                if local_data["subjects"]:

                    return local_data

            except Exception:

                pass

        if "429" in error_text:

            friendly_error = (
                "Gemini API quota or rate limit exceeded. "
                "Please wait and try again."
            )

        elif "503" in error_text:

            friendly_error = (
                "Gemini is temporarily overloaded. "
                "Please try again later."
            )

        elif "504" in error_text:

            friendly_error = (
                "Gemini processing deadline exceeded."
            )

        elif (
            "timeout" in error_text.lower()
            or "timed out" in error_text.lower()
        ):

            friendly_error = (
                "Gemini request timed out."
            )

        else:

            friendly_error = (
                "Marksheet analysis failed."
            )

        return {

            "error": friendly_error,

            "error_type": error_type,

            "details": error_text

        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("======================================")
    print("UNIVERSAL ACADEMIC AI")
    print("MARKSHEET ANALYZER")
    print("======================================")

    print("Local OCR: EasyOCR")
    print("Fallback: Gemini Vision")
    print("Image Optimization: Enabled")
    print("Performance Tracking: Enabled")
    print("======================================")

    print("MARKSHEET AGENT READY")
