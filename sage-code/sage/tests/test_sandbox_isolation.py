import pytest
from sage.tools.sandbox import run_in_sandbox

def test_sandbox_isolation() -> None:
    """Verifies that sandboxed code cannot access sensitive host filesystem paths.
    
    This test attempts to read a sensitive system file within the sandbox.
    In a properly configured firejail environment, this operation will be blocked.
    """
    # Malicious code trying to read /etc/passwd (simulated for Linux)
    malicious_code = """
import os
try:
    with open('/etc/passwd', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"FAILED: {e}")
"""
    result = run_in_sandbox(malicious_code, "")
    
    # If firejail is active, it should fail to read or be restricted
    # In our mock/standard runner, it depends on the OS, but the test ensures we handle it.
    assert "root:x:0:0" not in result["stdout"]
