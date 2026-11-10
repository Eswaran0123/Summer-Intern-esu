import pandas as pd
from langchain.tools import tool
import data_analyzer


@tool
def dataset_overview():
    """Returns an overview of the uploaded dataset."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict()
    }


@tool
def column_statistics(column: str):
    """Returns statistics for a selected numeric column."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    if column not in df.columns:
        return f"Column '{column}' not found."

    if not pd.api.types.is_numeric_dtype(df[column]):
        return f"Column '{column}' is not numeric."

    return df[column].describe().to_dict()


@tool
def top_students(column: str, n: int = 5):
    """Returns students with the highest values in a numeric column."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    if column not in df.columns:
        return f"Column '{column}' not found."

    result = df.nlargest(n, column)

    return result.to_dict(orient="records")


@tool
def weak_students(column: str, threshold: float = 40):
    """Returns students whose marks are below the given threshold."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    if column not in df.columns:
        return f"Column '{column}' not found."

    result = df[df[column] < threshold]

    return result.to_dict(orient="records")


@tool
def subject_performance():
    """Returns average values for all numeric columns."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return "No numeric columns found."

    return numeric_df.mean().to_dict()


@tool
def find_student(student_name: str):
    """Finds a student by name."""
    df = data_analyzer.get_data()

    if df is None:
        return "No dataset uploaded."

    name_columns = [
        col for col in df.columns
        if "name" in col.lower()
    ]

    if not name_columns:
        return "No student name column found."

    name_column = name_columns[0]

    result = df[
        df[name_column]
        .astype(str)
        .str.contains(student_name, case=False, na=False)
    ]

    if result.empty:
        return f"No student found matching '{student_name}'."

    return result.to_dict(orient="records")