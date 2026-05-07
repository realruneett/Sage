import hashlib
import time
from loguru import logger

class SageCodeXAI:
    """SAGE-CODE XAI module for reasoning audit logs."""
    def __init__(self):
        self.log = []

    def log_reasoning(self, node: str, content: str):
        entry = {
            "timestamp": time.time(),
            "node": node,
            "content": content
        }
        self.log.append(entry)
        logger.info(f"[XAI][{node}] {content[:100]}...")

    def get_audit_trail(self) -> str:
        return "\n".join([f"{e['node']}: {e['content']}" for e in self.log])

    def generate_proof_of_work(self, result: str) -> str:
        """Timestamps the synthesis with a PoW hash."""
        ts = str(time.time())
        payload = f"{result}|{ts}"
        h = hashlib.sha256(payload.encode()).hexdigest()
        return f"POW-{h[:12]}-{ts}"
