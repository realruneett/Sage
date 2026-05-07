import numpy as np
from sage.core.aode import torsion_warp
from typing import List

class TorsionGenerator:
    """Generates orthogonal architectural nudges (torsion warps).

    This module maps architectural design vectors to perpendicular idioms,
    forcing the Implementer to explore alternative solution manifolds.
    """
    def __init__(self, library_path: str = "sage/prompts/torsion_suffixes.md") -> None:
        """Loads the library of orthogonal constraints.
        
        Args:
            library_path: Path to the markdown file containing torsion suffixes.
        """
        try:
            with open(library_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.suffixes = [l.strip().split(": ", 1)[-1].strip('"') for l in lines if '"' in l]
        except Exception:
            # Fallback to a set of core defaults if the library is missing
            self.suffixes = [
                "Prefer functional/immutable patterns.",
                "Prefer iterative over recursive logic.",
                "Prefer async/non-blocking I/O."
            ]

    def get_orthogonal_nudge(self, design_vec: np.ndarray) -> str:
        """Computes a warped vector and selects an orthogonal idiom nudge.

        Args:
            design_vec: The original design vector from the Architect.

        Returns:
            A string suffix representing the orthogonal constraint.
        """
        if not self.suffixes:
            return "Focus on idiomatic performance."
            
        # Warp the vector along a perpendicular manifold
        warped = torsion_warp(design_vec)
        
        # Deterministically select a suffix based on the warp projection
        idx = int(abs(np.sum(warped)) * 1000) % len(self.suffixes)
        return self.suffixes[idx]
