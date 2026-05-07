from hypothesis import strategies as st
from typing import List, Any

def generate_hypothesis_strategy(type_name: str) -> Any:
    """Generates a basic hypothesis strategy for the Red-Team's property tests.

    Args:
        type_name: The name of the Python type (e.g., 'str', 'int').

    Returns:
        A hypothesis strategy object for the requested type.
    """
    if type_name == "str":
        return st.text()
    if type_name == "int":
        return st.integers()
    if type_name == "float":
        return st.floats(allow_nan=False, allow_infinity=False)
    if type_name == "dict":
        return st.dictionaries(st.text(), st.text())
    return st.nothing()
