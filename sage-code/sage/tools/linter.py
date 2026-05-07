import subprocess
import json
from typing import List, Dict, Any

def run_ruff(code: str) -> List[Dict[str, Any]]:
    """Runs ruff on the provided code and returns a list of violations.

    Args:
        code: The Python source code to lint.

    Returns:
        A list of dictionaries representing ruff violations, or an empty list.
    """
    try:
        # Use stdin to avoid temporary files
        result = subprocess.run(
            ["ruff", "check", "-", "--format", "json"],
            input=code,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else []
        return []
    except Exception:
        return []
