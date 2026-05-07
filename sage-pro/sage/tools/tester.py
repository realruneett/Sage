import asyncio
from typing import Dict, Any
from sage.tools.sandbox import run_in_sandbox

def run_pytest(code: str, tests: str) -> Dict[str, Any]:
    """Runs pytest in the firejail sandbox to verify code against generated tests.

    Args:
        code: The implementation code to test.
        tests: The test code (pytest format).

    Returns:
        Dict containing execution results and coverage metadata.
    """
    # The sandbox runner handles the file creation and isolation
    return run_in_sandbox(code, tests)
