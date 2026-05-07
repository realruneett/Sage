import pytest
import numpy as np
from sage.core.aode import CodeProposal, lie_bracket_synthesis

def test_lie_bracket_nonzero():
    """
    Asserts that [ABC] - [ACB] != 0, proving non-abelian synthesis.
    """
    vec_abc = np.random.randn(1024)
    vec_acb = np.random.randn(1024)
    
    out_abc = CodeProposal(code="ABC", tests="", vector=vec_abc, cycle=0)
    out_acb = CodeProposal(code="ACB", tests="", vector=vec_acb, cycle=0)
    
    _, divergence = lie_bracket_synthesis(out_abc, out_acb)
    
    assert divergence > 1e-3
