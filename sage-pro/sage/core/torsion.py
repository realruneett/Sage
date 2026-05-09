"""
SAGE-PRO Semantic Torsion Module
════════════════════════════════
Implements the Torsion Tensor T^λ_{μν} ≠ 0 to warp the generative path
away from the baseline geodesic.

Two levels of enforcement:
  1. Prompt-level: Orthogonal suffix selected via min|cos(θ)| (Gram-Schmidt)
  2. Logit-level: Token ID penalties applied via vLLM logit_bias field

    P(token | context) = softmax(logits − Penalty(token ∈ Baseline_Tokens))
"""

import numpy as np
import structlog
from typing import Dict, Tuple

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────
#  Torsion Penalty Map — maps each axis label to (token_id, penalty)
#  Token IDs are approximate GPT-2/Llama vocab entries for the concept.
#  Penalties in range [-5.0, -1.0] — negative = discourage token.
# ─────────────────────────────────────────────────────────────────────

TORSION_PENALTY_MAP: Dict[str, Dict[int, float]] = {
    "oop_vs_functional": {
        # Penalize functional-style tokens to push toward OOP
        3929:  -3.0,   # "lambda"
        8899:  -2.5,   # "map"
        3001:  -2.5,   # "filter"
        7532:  -2.0,   # "reduce"
        1441:  -1.5,   # "yield"
        11451: -1.5,   # "comprehension" fragment
    },
    "iteration_vs_recursion": {
        # Penalize recursion patterns to push toward iteration
        7:     -2.0,   # "return" (recursive returns)
        2134:  -3.5,   # "recur"
        1109:  -2.0,   # "self" (self-calls)
        13966: -3.0,   # "recursive"
        5765:  -1.5,   # "stack" (call stack)
    },
    "async_vs_sync": {
        # Penalize async tokens to push toward sync
        9012:  -4.0,   # "async"
        25507: -4.0,   # "await"
        812:   -2.0,   # "coroutine" fragment
        7560:  -2.5,   # "asyncio"
        1441:  -2.0,   # "yield" (async generators)
    },
    "generic_vs_specialized": {
        # Penalize specialized/concrete tokens to push toward generics
        4906:  -2.0,   # "int"
        5765:  -2.0,   # "str"
        9526:  -2.0,   # "float"
        2340:  -1.5,   # "list"
        15988: -2.5,   # "concrete"
    },
    "performance_vs_readability": {
        # Penalize readability tokens to push toward performance
        3670:  -2.0,   # "comment" fragment
        2474:  -1.5,   # "doc"
        764:   -1.0,   # "name"
        10618: -2.5,   # "readable"
        4686:  -1.5,   # "verbose"
    },
    "memory_vs_cpu": {
        # Penalize memory-heavy tokens to push toward CPU-efficient
        30073: -3.0,   # "cache"
        2340:  -2.0,   # "list"
        8633:  -2.0,   # "dict"
        17990: -2.5,   # "buffer"
        22506: -2.0,   # "alloc"
    },
    "defensive_vs_optimistic": {
        # Penalize optimistic patterns to push toward defensive
        1949:  -3.0,   # "pass" (bare except:pass)
        18224: -2.5,   # "ignore"
        4329:  -2.0,   # "skip"
        13047: -1.5,   # "assume"
        28552: -2.0,   # "trust"
    },
}


def torsion_to_logit_bias(torsion_label: str) -> Dict[int, float]:
    """Converts a torsion axis label to a vLLM logit_bias dict.

    Args:
        torsion_label: One of the 7 axis labels from TORSION_PENALTY_MAP.

    Returns:
        A dict mapping token IDs (int) to penalty floats (negative).
        Returns empty dict if the label is not recognized.
    """
    bias = TORSION_PENALTY_MAP.get(torsion_label, {})
    if not bias:
        logger.warning("torsion_label_not_found", label=torsion_label)
    return dict(bias)


def compute_torsion_suffix(
    design_text: str,
    embedder: any,
    suffix_library: Dict[str, str],
) -> Tuple[str, Dict[int, float]]:
    """Picks the torsion suffix most perpendicular to the current design
    AND generates the corresponding logit_bias for token-level enforcement.

    Uses cosine similarity to identify the nudge that provides the
    highest divergence (orthogonal projection) from the baseline manifold.

    Args:
        design_text: The architectural design text from the Architect.
        embedder: The SentenceTransformer model.
        suffix_library: A mapping of nudge labels to their markdown text.

    Returns:
        A tuple of (suffix_text, logit_bias_dict):
            - suffix_text: The selected torsion suffix string for prompt injection.
            - logit_bias_dict: Token penalties for vLLM logit_bias enforcement.
    """
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
    logit_bias = torsion_to_logit_bias(selected_label)

    logger.info(
        "torsion_suffix_selected",
        label=selected_label,
        ortho_score=float(ortho_scores[best_idx]),
        logit_bias_count=len(logit_bias),
    )

    return suffixes[best_idx], logit_bias
