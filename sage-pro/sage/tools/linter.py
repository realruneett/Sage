import asyncio
import json
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

async def run_ruff(path: str) -> List[Dict[str, Any]]:
    \"\"\"Invokes Ruff linter on the specified path and returns findings.

    Args:
        path: The filesystem path (file or directory) to lint.

    Returns:
        A list of dictionaries containing ruff violations.
        Each finding includes: rule, severity, line, and message.
    \"\"\"
    cmd = ["ruff", "check", "--output-format=json", path]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if not stdout:
            return []

        findings = json.loads(stdout)
        formatted_findings = []
        
        for f in findings:
            formatted_findings.append({
                "rule": f.get("code"),
                "severity": "error" if f.get("fix") is None else "warning",
                "line": f.get("location", {}).get("row"),
                "message": f.get("message")
            })
            
        return formatted_findings

    except Exception as e:
        logger.error("ruff_lint_failed", error=str(e))
        return []
