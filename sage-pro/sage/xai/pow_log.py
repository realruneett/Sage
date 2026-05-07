import json
import time

def log_pow_timestamp(pow_hash: str, task_id: str):
    """Appends a PoW timestamp to the local ledger."""
    entry = {
        "task_id": task_id,
        "pow_hash": pow_hash,
        "recorded_at": time.time()
    }
    with open("sage/xai/pow_ledger.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
