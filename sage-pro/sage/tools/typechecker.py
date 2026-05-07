import asyncio
import json
import structlog
import re
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

async def run_mypy(path: str) -> List[Dict[str, Any]]:
    \"\"\"Invokes Mypy type checker on the specified path and returns findings.

    Args:
        path: The filesystem path to type check.

    Returns:
        A list of dictionaries containing type violations.
    \"\"\"
    # Mypy JSON output is supported in newer versions via --output=json
    cmd = ["mypy", "--strict", "--no-color-output", "--no-error-summary", "--output=json", path]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if not stdout:
            return []

        try:
            # Attempt JSON parsing
            findings = json.loads(stdout)
            return [
                {
                    "rule": f.get("code"),
                    "severity": f.get("severity"),
                    "line": f.get("line"),
                    "message": f.get("message")
                }
                for f in findings
            ]
        except json.JSONDecodeError:
            # Fallback to text parsing for older mypy versions or non-json output
            text_output = stdout.decode("utf-8")
            findings = []
            for line in text_output.splitlines():
                # Format: file:line: severity: message [code]
                match = re.match(r\".*:(?P<line>\\d+): (?P<severity>\\w+): (?P<message>.*) \\[(?P<code>.*)\\]\", line)
                if match:
                    findings.append(match.groupdict())
            return findings

    except Exception as e:
        logger.error("mypy_check_failed", error=str(e))
        return []
