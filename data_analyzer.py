import pandas as pd

# Separate storage for the currently active dataset
_current_data = None
_current_filename = None


def set_data(dataframe, filename=None):
    global _current_data
    global _current_filename

    if dataframe is None:
        return

    _current_data = dataframe.copy()
    _current_filename = filename


def get_data():
    return _current_data


def get_filename():
    return _current_filename


def clear_data():
    global _current_data
    global _current_filename

    _current_data = None
    _current_filename = None