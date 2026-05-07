import subprocess
import os
import tempfile
from typing import Dict, Any

def run_in_sandbox(code: str, test_code: str = "", timeout: int = 30) -> Dict[str, Any]:
    """Runs untrusted code and tests in a firejail-sandboxed subprocess.

    Args:
        code: The implementation code to run.
        test_code: The test code to append to the implementation.
        timeout: Maximum execution time in seconds.

    Returns:
        Dict containing stdout, stderr, exit_code, and success status.

    Raises:
        RuntimeError: If execution fails outside the sandbox logic.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")
        
        with open(code_path, "w") as f:
            f.write(code)
        
        full_code = code + "\n\n" + test_code
        with open(test_path, "w") as f:
            f.write(full_code)
            
        try:
            # Use firejail if present for better isolation
            cmd = ["python3", test_path]
            if subprocess.run(["which", "firejail"], capture_output=True).returncode == 0:
                cmd = ["firejail", "--quiet", "--net=none", "--private", "python3", test_path]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout", "exit_code": 124}
        except Exception as e:
            return {"success": False, "error": str(e), "exit_code": 1}
