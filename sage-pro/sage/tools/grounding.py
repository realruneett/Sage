from sage.tools.linter import run_ruff
from sage.tools.typechecker import run_mypy
from sage.tools.security import run_security_scan
from sage.tools.sandbox import run_in_sandbox
from sage.tools.complexity import analyze_complexity
from typing import Dict, Any

async def evaluate_code(code: str, tests: str) -> Dict[str, Any]:
    """Runs the mechanical tool oracle and computes a unified damage score.

    This function aggregates findings from the linter, type-checker, security 
    scanner, sandbox execution, and complexity analyzer.

    Args:
        code: The Python implementation code to evaluate.
        tests: The test cases to run against the code.

    Returns:
        Dict containing the tool findings and the aggregated damage score.
    """
    # Parallel tool execution could be implemented here for speed
    ruff_res = run_ruff(code)
    mypy_res = run_mypy(code)
    sec_res = run_security_scan(code)
    sandbox_res = run_in_sandbox(code, tests)
    comp_res = analyze_complexity(code)
    
    # Calculate damage (0.0 to 1.0+)
    # This represents the 'Damage Function' from the Nash Crucible.
    damage = 0.0
    damage += len(ruff_res) * 0.1
    damage += len(mypy_res) * 0.4
    damage += len(sec_res.get("bandit", [])) * 0.8
    damage += (0.0 if sandbox_res.get("success") else 1.0)
    damage += max(0, (comp_res.get("avg_cyclomatic_complexity", 0) - 10) * 0.2)
    
    return {
        "total_damage": min(damage, 2.0),
        "ruff": ruff_res,
        "mypy": mypy_res,
        "security": sec_res,
        "sandbox": sandbox_res,
        "complexity": comp_res
    }
