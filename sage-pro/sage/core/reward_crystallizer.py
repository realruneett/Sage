"""
SAGE-PRO Reward Crystallizer
═════════════════════════════
Computes composite reward signal from multi-dimensional quality metrics.

R = w_correctness × correctness
  + w_security   × security
  + w_efficiency  × efficiency
  + w_novelty     × novelty

Weights loaded from configs/aode_hyperparams.yaml → ctr_maqr.reward_weights.
"""

import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)


class RewardCrystallizer:
    """Computes composite reward from multi-dimensional quality scores."""

    def __init__(self, hyperparams: Dict[str, Any]) -> None:
        """Initializes reward weights from config.

        Args:
            hyperparams: Full hyperparams dict (expects 'ctr_maqr.reward_weights').
        """
        cfg = hyperparams.get("ctr_maqr", {})
        rw = cfg.get("reward_weights", {})

        self.w_correctness: float = rw.get("correctness", 0.40)
        self.w_security: float = rw.get("security", 0.30)
        self.w_efficiency: float = rw.get("efficiency", 0.20)
        self.w_novelty: float = rw.get("novelty", 0.10)

        logger.info(
            "reward_crystallizer_initialized",
            weights={
                "correctness": self.w_correctness,
                "security": self.w_security,
                "efficiency": self.w_efficiency,
                "novelty": self.w_novelty,
            },
        )

    def compute(
        self,
        correctness: float,
        security: float,
        efficiency: float,
        novelty: float,
    ) -> float:
        """Computes the composite reward score.

        All input scores should be in [0, 1].

        Args:
            correctness: How correct is the generated code (tests pass rate).
            security: Security score (1 - vulnerability density).
            efficiency: Big-O / runtime efficiency score.
            novelty: Novelty of the approach vs. prior solutions.

        Returns:
            Composite reward in [0, 1].
        """
        reward = (
            self.w_correctness * correctness
            + self.w_security * security
            + self.w_efficiency * efficiency
            + self.w_novelty * novelty
        )

        # Clamp to [0, 1]
        reward = max(0.0, min(1.0, reward))

        logger.info(
            "reward_computed",
            correctness=correctness,
            security=security,
            efficiency=efficiency,
            novelty=novelty,
            composite=reward,
        )
        return reward
