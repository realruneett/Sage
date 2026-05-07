import subprocess
import time
from typing import Dict, Any

def run_performance_benchmark(code_path: str) -> Dict[str, Any]:
    """Runs high-precision performance benchmarks using hyperfine.

    Args:
        code_path: Path to the generated code file to benchmark.

    Returns:
        Dict containing benchmarking output or error messages.
    """
    try:
        # Benchmark the execution of the generated solution
        result = subprocess.run(
            ["hyperfine", "--warmup", "3", f"python3 {code_path}"],
            capture_output=True,
            text=True,
            check=False
        )
        return {"output": result.stdout, "success": result.returncode == 0}
    except Exception as e:
        return {"error": str(e), "success": False}
