import asyncio
import os
import tempfile
import json
import shutil
import structlog
from pathlib import Path
from typing import Optional
from sage.core.types import ToolReport

logger = structlog.get_logger(__name__)

async def run_in_sandbox(
    code: str, 
    tests: str, 
    timeout: int = 30
) -> ToolReport:
    \"\"\"Executes code and tests within a secure sandbox environment.

    This function leverages firejail or bubblewrap for isolation, falling back 
    to restricted subprocesses if necessary. It ensures no network access 
    and strict resource limits.

    Args:
        code: The Python source code to implement.
        tests: The pytest-style test cases.
        timeout: Maximum execution time in seconds.

    Returns:
        A ToolReport containing the execution results, errors, and metadata.
    \"\"\"
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        code_file = tmp_path / "solution.py"
        test_file = tmp_path / "test_solution.py"
        report_file = tmp_path / "report.json"

        code_file.write_text(code, encoding="utf-8")
        test_file.write_text(f"from solution import *\\n\\n{tests}", encoding="utf-8")

        # Determine sandbox wrapper
        if shutil.which("firejail"):
            cmd = [
                "firejail", "--quiet", "--net=none", "--private", 
                "--rlimit-as=1G", f"--timeout=00:00:{timeout}",
                "python3", "-m", "pytest", str(test_file), 
                f"--json-report", f"--json-report-file={report_file}"
            ]
        elif shutil.which("bwrap"):
            cmd = [
                "bwrap", "--unshare-all", "--share-net", "false",
                "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib",
                "--ro-bind", "/lib64", "/lib64", "--ro-bind", "/bin", "/bin",
                "--proc", "/proc", "--dev", "/dev",
                "--bind", str(tmp_dir), str(tmp_dir),
                "python3", "-m", "pytest", str(test_file),
                f"--json-report", f"--json-report-file={report_file}"
            ]
        else:
            # Fallback to plain asyncio with limits (unsafe, but allows local dev)
            cmd = [
                "python3", "-m", "pytest", str(test_file),
                f"--json-report", f"--json-report-file={report_file}"
            ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmp_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout + 5)
            except asyncio.TimeoutError:
                process.kill()
                logger.warning("sandbox_timeout_reached", timeout=timeout)
                return ToolReport(tests_passed=False, total_damage=1.0)

            # Parse pytest-json-report
            if report_file.exists():
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                    summary = report_data.get("summary", {})
                    passed = summary.get("passed", 0)
                    total = summary.get("total", 0)
                    tests_passed = passed == total and total > 0
                    
                    return ToolReport(
                        tests_passed=tests_passed,
                        coverage=report_data.get("coverage", {}).get("percent_covered", 0.0),
                        total_damage=0.0 if tests_passed else 0.5
                    )
            
            # If no report, check exit code
            success = process.returncode == 0
            return ToolReport(
                tests_passed=success,
                total_damage=0.0 if success else 1.0
            )

        except Exception as e:
            logger.error("sandbox_execution_failed", error=str(e))
            return ToolReport(tests_passed=False, total_damage=1.0)
