"""Best-effort W&B logging. No-ops when wandb is not installed or unkeyed.

A failed wandb import or run never breaks retrain; the UI reads
``metrics_log.json`` either way.
"""

from __future__ import annotations

from typing import Any, Dict, List

import config

_LAST_STATUS: Dict[str, Any] = {"status": "not_called"}


def status() -> Dict[str, Any]:
    return dict(_LAST_STATUS)


def log_retrain(row: Dict[str, Any], scorer: Dict[str, Any], labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    global _LAST_STATUS
    if not config.WANDB_API_KEY:
        _LAST_STATUS = {"status": "skipped", "reason": "WANDB_API_KEY_missing"}
        return status()
    try:
        import wandb  # type: ignore
    except Exception as exc:
        _LAST_STATUS = {"status": "error", "error": type(exc).__name__}
        return status()
    try:
        settings = wandb.Settings(init_timeout=20)
        run = wandb.init(
            project=config.WANDB_PROJECT or "scribner",
            entity=config.WANDB_TEAM or None,
            job_type="retrain",
            reinit=True,
            mode="online",
            settings=settings,
        )
        wandb.log({k: v for k, v in row.items() if isinstance(v, (int, float))})
        run.summary["n_labels"] = len(labels)
        run.summary["scorer_n"] = scorer.get("n")
        run.summary["andon_line"] = row.get("andon_line") or ""
        run_id = str(getattr(run, "id", "") or "")
        run.finish()
        _LAST_STATUS = {"status": "ok", "run_id": run_id}
    except Exception as exc:
        _LAST_STATUS = {"status": "error", "error": type(exc).__name__}
    return status()
