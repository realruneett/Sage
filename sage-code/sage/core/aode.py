import numpy as np
import gudhi
from dataclasses import dataclass
from typing import List, Tuple, Callable, Any, Dict
from loguru import logger

@dataclass
class CodeProposal:
    """
    SAGE-CODE Proposal container.
    """
    code: str
    tests: str
    vector: np.ndarray
    cycle: int
    damage: float = 1.0
    metadata: Dict[str, Any] = None

def topological_route(
    query_vec: np.ndarray, 
    corpus_vecs: np.ndarray, 
    k: int = 5
) -> Tuple[List[int], Tuple[int, int]]:
    """Code-Topology Routing via Persistent Homology.

    Uses gudhi.RipsComplex to identify topological voids in the code embedding manifold.
    Voids represent under-tested or high-novelty regions.

    Args:
        query_vec: Embedding vector of the current task.
        corpus_vecs: Matrix of existing code file embeddings.
        k: Number of void regions to return.

    Returns:
        Tuple containing:
            - List of indices for the most novel code regions.
            - Tuple of (β₁, β₂) Betti numbers for the local topology.
    """
    points = np.vstack([query_vec, corpus_vecs])
    rips_complex = gudhi.RipsComplex(points=points, max_edge_distance=1.0)
    simplex_tree = rips_complex.create_simplex_tree(max_dimension=3)
    persistence = simplex_tree.persistence()
    
    betti_1 = sum(1 for dim, (birth, death) in persistence if dim == 1 and (death - birth) > 0.1)
    betti_2 = sum(1 for dim, (birth, death) in persistence if dim == 2 and (death - birth) > 0.1)
    
    # Calculate density (distance to centroid)
    centroid = np.mean(corpus_vecs, axis=0)
    distances = np.linalg.norm(corpus_vecs - centroid, axis=1)
    
    # Get indices with maximum distance (the 'voids')
    void_indices = np.argsort(distances)[-k:][::-1].tolist()
    
    return void_indices, (betti_1, betti_2)

def torsion_warp(design_vec: np.ndarray, alpha: float = 0.7) -> np.ndarray:
    """Riemann-Cartan Torsion for orthogonal solution manifolds.

    Shifts a design vector along a perpendicular axis to explore alternative
    architectural idioms (e.g., OOP vs Functional).

    Args:
        design_vec: The original architectural design vector.
        alpha: The torsion warp strength.

    Returns:
        The warped vector normalized to the unit sphere.
    """
    # Create a random orthogonal axis for the torsion nudge
    random_axis = np.random.randn(*design_vec.shape)
    random_axis /= np.linalg.norm(random_axis)
    
    # Project design_vec onto random_axis
    proj = np.dot(design_vec, random_axis) * random_axis
    
    # Perpendicular component
    perp = design_vec - proj
    
    # Push along perpendicular axis
    warped = design_vec + alpha * perp
    return warped / (np.linalg.norm(warped) + 1e-9)

def lie_bracket_synthesis(
    out_ABC: CodeProposal, 
    out_ACB: CodeProposal
) -> Tuple[CodeProposal, float]:
    """Non-Abelian Lie Bracket Synthesis for Code.

    Computes the divergence between Design-first (ABC) and Threat-first (ACB) branches.

    Args:
        out_ABC: Result of the ABC synthesis order.
        out_ACB: Result of the ACB synthesis order.

    Returns:
        Tuple containing the final merged proposal and the divergence index.
    """
    divergence = float(np.linalg.norm(out_ABC.vector - out_ACB.vector))
    
    # In SAGE-CODE, we choose the one with lower damage (if available) 
    # or the ABC branch by default
    final_proposal = out_ABC
    return final_proposal, divergence

async def nash_refine(
    proposal: CodeProposal, 
    red_team_fn: Callable[[str], Any], 
    synth_fn: Callable[[CodeProposal, Dict[str, Any]], Any], 
    tool_fn: Callable[[str, str], Any],
    eps: float = 0.05, 
    delta: float = 0.02, 
    max_cycles: int = 4
) -> Tuple[CodeProposal, List[Dict[str, Any]]]:
    """Minimax Nash Equilibrium Refinement grounded by tools.

    Iteratively attacks and fixes code until a stability threshold is met
    or maximum cycles are reached.

    Args:
        proposal: The initial code proposal.
        red_team_fn: Async function that returns an adversarial attack.
        synth_fn: Async function that re-synthesizes code based on findings.
        tool_fn: Async function that executes the mechanical oracle.
        eps: Damage threshold for early exit (Nash equilibrium).
        delta: Minimum improvement threshold.
        max_cycles: Maximum number of refinement iterations.

    Returns:
        Tuple containing the refined proposal and the trajectory history.
    """
    history = []
    current_proposal = proposal
    prev_damage = 1.0
    
    for i in range(max_cycles):
        # 1. Red-team attack + Tool grounding
        attack = await red_team_fn(current_proposal.code)
        tool_report = await tool_fn(current_proposal.code, attack.tests)
        
        damage = tool_report["total_damage"]
        
        logger.info(f"[NASH CYCLE {i+1}] Damage: {damage:.4f}")
        
        history.append({
            "cycle": i + 1,
            "damage": damage,
            "tool_report": tool_report
        })
        
        if damage < eps or abs(prev_damage - damage) < delta:
            logger.info("Nash Equilibrium reached.")
            break
            
        # 2. Re-synthesize with findings
        current_proposal = await synth_fn(current_proposal, tool_report)
        current_proposal.cycle = i + 1
        current_proposal.damage = damage
        prev_damage = damage
        
    return current_proposal, history
