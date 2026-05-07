import pytest
import numpy as np
from sage.core.aode import topological_route, torsion_warp, CodeProposal

def test_topological_route() -> None:
    """Verifies that topological routing identifies the k-most novel regions."""
    query = np.random.randn(1024)
    corpus = np.random.randn(20, 1024)
    indices, (b1, b2) = topological_route(query, corpus, k=5)
    assert len(indices) == 5
    assert isinstance(b1, int)
    assert isinstance(b2, int)

def test_torsion_warp() -> None:
    """Verifies that torsion warping produces a distinct unit vector."""
    vec = np.random.randn(1024)
    warped = torsion_warp(vec, alpha=0.5)
    assert np.isclose(np.linalg.norm(warped), 1.0)
    assert not np.array_equal(vec, warped)

def test_code_proposal() -> None:
    """Verifies the CodeProposal data structure."""
    p = CodeProposal(code="print(1)", tests="assert 1", vector=np.zeros(10), cycle=0)
    assert p.damage == 1.0
    assert p.code == "print(1)"

def test_lie_bracket_divergence() -> None:
    """Verifies that the Lie bracket correctly computes synthesis divergence."""
    from sage.core.aode import lie_bracket_synthesis
    v1 = np.ones(10)
    v2 = np.zeros(10)
    p1 = CodeProposal("A", "", v1, 0)
    p2 = CodeProposal("B", "", v2, 0)
    _, div = lie_bracket_synthesis(p1, p2)
    assert div > 3.0 # norm of sqrt(10)
