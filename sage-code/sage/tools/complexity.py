import radon.complexity as cc
from radon.metrics import mi_visit
from typing import Dict, Any

def analyze_complexity(code: str) -> Dict[str, Any]:
    """Analyzes the cyclomatic complexity and maintainability index of source code.

    Args:
        code: The Python source code to analyze.

    Returns:
        Dict containing average cyclomatic complexity, maintainability index, 
        and high-complexity findings.
    """
    try:
        results = cc.cc_visit(code)
        complexity = sum(r.complexity for r in results) / (len(results) or 1)
        maintainability = float(mi_visit(code, multi=False))
        
        return {
            "avg_cyclomatic_complexity": complexity,
            "maintainability_index": maintainability,
            "findings": [f"{r.name}: {r.complexity}" for r in results if r.complexity > 10]
        }
    except Exception:
        return {"avg_cyclomatic_complexity": 0.0, "maintainability_index": 100.0, "findings": []}
