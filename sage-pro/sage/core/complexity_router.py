import re
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)

STRATEGIES = {
    "simple": {"max_cycles": 1, "epsilon": 0.5},
    "medium": {"max_cycles": 2, "epsilon": 0.15},
    "complex": {"max_cycles": 4, "epsilon": 0.05},
}

def classify_complexity(query: str) -> str:
    q = query.lower().strip()
    words = q.split()
    wc = len(words)
    simple_re = re.compile(r'\b(hi|hello|hey|thanks|what is|explain|define|who is)\b', re.I)
    complex_re = re.compile(r'\b(architect|system design|distributed|microservice|optimize|refactor|production|security|algorithm|implement.*from scratch)\b', re.I)
    if wc <= 8 and simple_re.search(q):
        return "simple"
    if wc > 60 or len(complex_re.findall(q)) >= 2:
        return "complex"
    if wc > 20:
        return "medium"
    if wc <= 5:
        return "simple"
    return "medium"

def get_strategy(query: str) -> Dict[str, Any]:
    tier = classify_complexity(query)
    strategy = STRATEGIES[tier].copy()
    strategy["tier"] = tier
    logger.info("complexity_classified", tier=tier, query=query[:60], word_count=len(query.split()))
    return strategy
