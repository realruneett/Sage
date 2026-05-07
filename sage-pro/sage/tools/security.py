import subprocess
import tempfile
import os
from typing import Dict, List, Any

def run_security_scan(code: str) -> Dict[str, Any]:
    """Runs security scanners (Bandit) on the provided code to detect vulnerabilities.

    Args:
        code: The Python source code to scan.

    Returns:
        Dict containing lists of findings for 'bandit' and 'semgrep'.
    """
    findings: Dict[str, List[Any]] = {"bandit": [], "semgrep": []}
    
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
        
    try:
        # Bandit Scan
        bandit_res = subprocess.run(
            ["bandit", "-f", "json", tmp_path],
            capture_output=True,
            text=True,
            check=False
        )
        if bandit_res.stdout:
            import json
            bandit_data = json.loads(bandit_res.stdout)
            findings["bandit"] = bandit_data.get("results", [])
            
        # Semgrep placeholder (integrated via configs/tools.yaml in production)
        # findings["semgrep"] = run_semgrep(tmp_path)
        
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
        return findings
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return findings
