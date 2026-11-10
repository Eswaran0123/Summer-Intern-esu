# ==========================================================
# MARKSHEET CALCULATOR
# ==========================================================


# ==========================================================
# 10TH / 12TH PERCENTAGE
# ==========================================================

def calculate_percentage(total_marks, maximum_marks):
    """
    Calculate percentage from obtained and maximum marks.
    """

    if maximum_marks == 0:
        return 0

    return round((total_marks / maximum_marks) * 100, 2)


# ==========================================================
# TNEA ENGINEERING CUTOFF
# ==========================================================

def calculate_engineering_cutoff(
    maths,
    physics,
    chemistry,
    maths_max=100,
    physics_max=100,
    chemistry_max=100
):
    """
    TNEA engineering cutoff out of 200.

    Mathematics = 100 marks
    Physics = 50 marks
    Chemistry = 50 marks
    """

    maths_cutoff = (maths / maths_max) * 100
    physics_cutoff = (physics / physics_max) * 50
    chemistry_cutoff = (chemistry / chemistry_max) * 50

    cutoff = (
        maths_cutoff +
        physics_cutoff +
        chemistry_cutoff
    )

    return round(cutoff, 2)


# ==========================================================
# SGPA
# ==========================================================

def calculate_sgpa(subjects):
    """
    Calculate SGPA using:

    SGPA = Sum(Credit × Grade Point) / Sum(Credits)

    subjects should contain:
    credits
    grade_point
    """

    total_credit_points = 0
    total_credits = 0

    for subject in subjects:

        credits = subject.get("credits")
        grade_point = subject.get("grade_point")

        if credits is None or grade_point is None:
            continue

        credits = float(credits)
        grade_point = float(grade_point)

        total_credit_points += credits * grade_point
        total_credits += credits

    if total_credits == 0:
        return None

    return round(
        total_credit_points / total_credits,
        2
    )


# ==========================================================
# CGPA
# ==========================================================

def calculate_cgpa(semesters):
    """
    Calculate CGPA using semester credits.

    Each semester should contain:
    sgpa
    credits
    """

    total_points = 0
    total_credits = 0

    for semester in semesters:

        sgpa = semester.get("sgpa")
        credits = semester.get("credits")

        if sgpa is None or credits is None:
            continue

        sgpa = float(sgpa)
        credits = float(credits)

        total_points += sgpa * credits
        total_credits += credits

    if total_credits == 0:
        return None

    return round(
        total_points / total_credits,
        2
    )


# ==========================================================
# SIMPLE CGPA
# ==========================================================

def calculate_average_cgpa(sgpa_values):
    """
    Used only when semester credit information
    is unavailable.

    This is an unweighted average.
    """

    if not sgpa_values:
        return None

    values = [
        float(value)
        for value in sgpa_values
        if value is not None
    ]

    if not values:
        return None

    return round(
        sum(values) / len(values),
        2
    )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("======================================")
    print("MARKSHEET CALCULATOR")
    print("======================================")

    percentage = calculate_percentage(
        450,
        500
    )

    print("10th/12th Percentage:", percentage)

    cutoff = calculate_engineering_cutoff(
        maths=90,
        physics=80,
        chemistry=85
    )

    print("Engineering Cutoff:", cutoff)

    subjects = [
        {
            "credits": 4,
            "grade_point": 9
        },
        {
            "credits": 3,
            "grade_point": 8
        },
        {
            "credits": 3,
            "grade_point": 10
        }
    ]

    sgpa = calculate_sgpa(subjects)

    print("SGPA:", sgpa)

    semesters = [
        {
            "sgpa": 8.5,
            "credits": 20
        },
        {
            "sgpa": 8.8,
            "credits": 22
        }
    ]

    cgpa = calculate_cgpa(semesters)

    print("CGPA:", cgpa)

    print("======================================")
    print("CALCULATOR READY")
    print("======================================")