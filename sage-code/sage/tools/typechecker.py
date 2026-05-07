import subprocess
import tempfile
import os
from typing import List

def run_mypy(code: str) -> List[str]:
    """Runs mypy --strict on the provided code to verify type safety.

    Args:
        code: The Python source code to check.

    Returns:
        A list of type errors found by mypy.
    """
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
        
    try:
        result = subprocess.run(
            ["mypy", "--strict", tmp_path],
            capture_output=True,
            text=True,
            check=False
        )
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
        if result.returncode != 0:
            return result.stdout.splitlines()
        return []
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return [str(e)]
