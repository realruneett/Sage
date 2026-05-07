import numpy as np
import structlog
from typing import Dict

logger = structlog.get_logger(__name__)

def compute_torsion_suffix(
    design_text: str, 
    embedder, 
    suffix_library: Dict[str, str]
) -> str:
    \"\"\"Picks the torsion suffix most perpendicular to the current design.

    Uses cosine similarity to identify the nudge that provides the 
    highest divergence (orthogonal projection) from the baseline manifold.

    Args:
        design_text: The architectural design text from the Architect.
        embedder: The SentenceTransformer model.
        suffix_library: A mapping of nudge labels to their markdown text.

    Returns:
        The selected torsion suffix string.
    \"\"\"
    design_vec = embedder.encode([design_text], convert_to_numpy=True)[0]
    
    suffixes = list(suffix_library.values())
    labels = list(suffix_library.keys())
    
    suffix_vecs = embedder.encode(suffixes, convert_to_numpy=True)
    
    # Calculate cosine similarity
    # Perpendicular means similarity close to 0
    dot_products = np.dot(suffix_vecs, design_vec)
    norms = np.linalg.norm(suffix_vecs, axis=1) * np.linalg.norm(design_vec)
    similarities = dot_products / (norms + 1e-9)
    
    # We want the one closest to 0 (most orthogonal)
    ortho_scores = np.abs(similarities)
    best_idx = np.argmin(ortho_scores)
    
    selected_label = labels[best_idx]
    logger.info("torsion_suffix_selected", label=selected_label, ortho_score=float(ortho_scores[best_idx]))
    
    return suffixes[best_idx]
