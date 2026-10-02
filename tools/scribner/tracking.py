"""Best-effort W&B logging. No-ops when wandb is not installed or unkeyed.

Agent note: a failed wandb import must never break retrain. The UI reads
``metrics_log.json`` either way.
"""

from __future__ import annotations

from typing import Any, Dict, List

import config


def log_retrain(row: Dict[str, Any], scorer: Dict[str, Any], labels: List[Dict[str, Any]]) -> None:
    if not config.WANDB_API_KEY:
        return
    try:
        import wandb  # type: ignore
    except Exception:
        return
    try:
        run = wandb.init(
            project=config.WANDB_PROJECT or "scribner",
            entity=config.WANDB_TEAM or None,
            job_type="retrain",
            reinit=True,
        )
        wandb.log({k: v for k, v in row.items() if isinstance(v, (int, float))})
        wandb.summary["n_labels"] = len(labels)
        wandb.summary["scorer_n"] = scorer.get("n")
        wandb.summary["andon_line"] = row.get("andon_line") or ""
        run.finish()
    except Exception:
        return
