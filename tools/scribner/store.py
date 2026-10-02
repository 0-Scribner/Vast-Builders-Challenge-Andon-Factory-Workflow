"""JSON file store under SCRIBNER_DATA_DIR.

Point SCRIBNER_DATA_DIR at a mounted volume to keep labels and the scorer
across restarts; the /app deployment mounts a PVC at /data. Scribner never
writes to VastDB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


class Store:
    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root or config.DATA_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.root / name

    def _read_json(self, name: str, default: Any) -> Any:
        p = self._path(name)
        if not p.exists():
            return default
        return json.loads(p.read_text(encoding="utf-8"))

    def _write_json(self, name: str, payload: Any) -> None:
        p = self._path(name)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        tmp.replace(p)

    def load_units(self) -> List[Dict[str, Any]]:
        return list(self._read_json("units.json", []))

    def save_units(self, units: List[Dict[str, Any]]) -> None:
        self._write_json("units.json", units)

    def load_labels(self) -> List[Dict[str, Any]]:
        p = self._path("labels.jsonl")
        if not p.exists():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def append_label(self, label: Dict[str, Any]) -> None:
        p = self._path("labels.jsonl")
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(label, default=str) + "\n")

    def replace_label_for_unit(self, unit_id: str, label: Dict[str, Any]) -> None:
        labels = [lab for lab in self.load_labels() if lab.get("unit_id") != unit_id]
        labels.append(label)
        p = self._path("labels.jsonl")
        p.write_text(
            "".join(json.dumps(lab, default=str) + "\n" for lab in labels),
            encoding="utf-8",
        )

    def load_decisions(self) -> List[Dict[str, Any]]:
        return list(self._read_json("decisions.json", []))

    def save_decisions(self, decisions: List[Dict[str, Any]]) -> None:
        self._write_json("decisions.json", decisions)

    def load_scorer(self) -> Optional[Dict[str, Any]]:
        return self._read_json("scorer.json", None)

    def save_scorer(self, scorer: Dict[str, Any]) -> None:
        self._write_json("scorer.json", scorer)

    def load_thresholds(self) -> Dict[str, float]:
        data = self._read_json("thresholds.json", None)
        if not data:
            return {"t_pass": 0.18, "t_fail": 0.82, "n_labels": 0.0}
        return data

    def save_thresholds(self, thresholds: Dict[str, float]) -> None:
        self._write_json("thresholds.json", thresholds)

    def load_metrics_log(self) -> List[Dict[str, Any]]:
        return list(self._read_json("metrics_log.json", []))

    def append_metrics(self, row: Dict[str, Any]) -> None:
        log = self.load_metrics_log()
        log.append(row)
        self._write_json("metrics_log.json", log)

    def state_summary(self) -> Dict[str, Any]:
        return {
            "data_dir": str(self.root),
            "n_units": len(self.load_units()),
            "n_labels": len(self.load_labels()),
            "n_decisions": len(self.load_decisions()),
            "thresholds": self.load_thresholds(),
            "has_scorer": self.load_scorer() is not None,
        }
