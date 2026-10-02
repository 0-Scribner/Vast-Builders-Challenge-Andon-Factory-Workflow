"""Japanese QC andon for the Pack C warehouse line.

TPS mapping (jidoka / mieruka / poka-yoke — not a translation sticker):

- 緑 正常   AUTO_CLEAR  — path is clear, line runs
- 黄 呼び出し HOLD      — andon cord: a human must look at the aisle clip
- 赤 停止   AUTO_ALERT  — near-miss / blocked path; do not auto-clear

The warehouse clip is the 現場 (gemba). The board is the 安灯.
False CLEAR is 重大不良: a red lamp must never become green without a human.

Mock mode paints three Pack C stand-in clips (empty aisle / hold / near-miss)
so the operator sees the lamp on the footage, not a grey rectangle.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from kits import CAMERA_ID, LOCATION, PACK_C_CAMERA, PAYOFF_QUERY, PRODUCT, STACK_LINE

LAMP_GREEN = "green"
LAMP_YELLOW = "yellow"
LAMP_RED = "red"

LAMP_JA = {
    LAMP_GREEN: "正常",
    LAMP_YELLOW: "呼び出し",
    LAMP_RED: "停止",
}
LAMP_ROMAJI = {
    LAMP_GREEN: "seijō",
    LAMP_YELLOW: "yobidashi",
    LAMP_RED: "teishi",
}
LAMP_EN = {
    LAMP_GREEN: "CLEAR / run",
    LAMP_YELLOW: "HOLD / call",
    LAMP_RED: "ALERT / stop",
}

STATION_JA = {
    "warehouse-aisle": "倉庫通路",
    "person-near-vehicle": "人対車両",
}

_RED_DECISIONS = {"AUTO_ALERT", "AUTO_FAIL", "UNSAFE"}
_YELLOW_DECISIONS = {"HOLD"}
_GREEN_DECISIONS = {"AUTO_CLEAR", "AUTO_PASS", "CLEAR"}

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

# Warehouse stand-in: racks + floor, tinted to the station lamp.
_CLIP = {
    LAMP_GREEN: {
        "bg": "0x0c1812",
        "floor": "0x1e3328",
        "rack": "0x3d4a3a",
        "fg": "0x1dff7a",
        "label": "正常 PATH CLEAR",
        "vehicle": False,
    },
    LAMP_YELLOW: {
        "bg": "0x221c0a",
        "floor": "0x3a3214",
        "rack": "0x5a4a20",
        "fg": "0xffd000",
        "label": "呼び出し HOLD",
        "vehicle": True,
    },
    LAMP_RED: {
        "bg": "0x1a0c0c",
        "floor": "0x3a1818",
        "rack": "0x5a2a2a",
        "fg": "0xff2a2a",
        "label": "停止 NEAR MISS",
        "vehicle": True,
    },
}


def lamp_for_decision(decision: Optional[str]) -> str:
    d = (decision or "").upper()
    if d in _RED_DECISIONS:
        return LAMP_RED
    if d in _YELLOW_DECISIONS or not d:
        return LAMP_YELLOW
    if d in _GREEN_DECISIONS:
        return LAMP_GREEN
    return LAMP_YELLOW


def decision_of(unit: Dict[str, Any]) -> str:
    return (unit.get("decision_row") or {}).get("decision") or unit.get("decision") or "HOLD"


def lamp_for_unit(unit: Optional[Dict[str, Any]]) -> str:
    if not unit:
        return LAMP_YELLOW
    return lamp_for_decision(decision_of(unit))


def counts(decisions: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    n_green = n_yellow = n_red = 0
    for d in decisions:
        lamp = lamp_for_decision(d.get("decision"))
        if lamp == LAMP_RED:
            n_red += 1
        elif lamp == LAMP_YELLOW:
            n_yellow += 1
        else:
            n_green += 1
    return {"green": n_green, "yellow": n_yellow, "red": n_red, "n": len(decisions)}


def line_lamp(queue: Sequence[Dict[str, Any]]) -> str:
    """Worst open ticket on the review queue. Empty queue → 正常."""
    worst = LAMP_GREEN
    for u in queue:
        lamp = lamp_for_unit(u)
        if lamp == LAMP_RED:
            return LAMP_RED
        if lamp == LAMP_YELLOW:
            worst = LAMP_YELLOW
    return worst


def _font() -> str:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return ""


def clip_path_for_lamp(lamp: str) -> Path:
    lamp = lamp if lamp in _CLIP else LAMP_YELLOW
    return Path(f"/tmp/scribner_andon_{lamp}.mp4")


def ensure_warehouse_clip(lamp: str) -> Path:
    """Pack C stand-in: aisle + racks, tinted to the andon lamp.

    Live mode streams the real VSS segment. Mock paints the gemba so the
    board and the footage share a color language.
    """
    lamp = lamp if lamp in _CLIP else LAMP_YELLOW
    path = clip_path_for_lamp(lamp)
    if path.exists() and path.stat().st_size > 1000:
        return path
    spec = _CLIP[lamp]
    font = _font()
    font_opt = f"fontfile={font}:" if font else ""
    aisle = (
        f"drawbox=x=0:y=400:w=960:h=140:color={spec['floor']}:t=fill,"
        f"drawbox=x=150:y=20:w=32:h=380:color={spec['rack']}:t=fill,"
        f"drawbox=x=778:y=20:w=32:h=380:color={spec['rack']}:t=fill,"
        f"drawbox=x=0:y=0:w=960:h=8:color={spec['fg']}:t=fill"
    )
    label = (
        f"{aisle},"
        f"drawtext={font_opt}text='sdg_warehouse_cam-2':"
        f"fontcolor=white:fontsize=22:x=24:y=24,"
        f"drawtext={font_opt}text='{spec['label']}':"
        f"fontcolor={spec['fg']}:fontsize=28:x=24:y=56"
    )
    cmd: List[str] = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={spec['bg']}:s=960x540:d=4.2:r=24",
    ]
    if spec["vehicle"]:
        cmd += ["-f", "lavfi", "-i", "color=c=0xf5a623:s=110x42:d=4.2:r=24"]
        cmd += [
            "-filter_complex",
            f"[0:v]{label}[aisle];[aisle][1:v]overlay=x='40+t*190':y=348:shortest=1[v]",
            "-map", "[v]",
        ]
    else:
        cmd += ["-vf", label]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "4.2",
        "-an", "-movflags", "+faststart", str(path),
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not path.exists() or path.stat().st_size < 100:
        path.write_bytes(b"")
    return path


def snapshot(
    *,
    decisions: Sequence[Dict[str, Any]],
    queue: Sequence[Dict[str, Any]],
    current: Optional[Dict[str, Any]] = None,
    camera_id: str = CAMERA_ID,
    location: str = LOCATION,
    pack: str = "C",
) -> Dict[str, Any]:
    tally = counts(decisions)
    line = line_lamp(queue)
    station_unit = current or (queue[0] if queue else None) or {}
    station_decision = decision_of(station_unit) if station_unit else "HOLD"
    station = lamp_for_decision(station_decision)
    kit_id = station_unit.get("kit_id") or "warehouse-aisle"
    insp = station_unit.get("inspection") or {}
    hazards = insp.get("hazards") or insp.get("missing") or []
    return {
        "board": "andon",
        "name_ja": "安灯",
        "jidoka": "自働化",
        "gemba": "現場",
        "poka_yoke": "ポカヨケ",
        "mieruka": "見える化",
        "product": PRODUCT,
        "payoff_query": PAYOFF_QUERY,
        "stack_line": STACK_LINE,
        "camera_id": camera_id or PACK_C_CAMERA,
        "location": location,
        "pack": pack,
        "station_ja": STATION_JA.get(kit_id, kit_id),
        "station_id": kit_id,
        "unit_id": station_unit.get("id"),
        "line_lamp": line,
        "line_ja": LAMP_JA[line],
        "line_romaji": LAMP_ROMAJI[line],
        "line_en": LAMP_EN[line],
        "station_lamp": station,
        "station_ja_lamp": LAMP_JA[station],
        "station_decision": station_decision or "HOLD",
        "counts": tally,
        "open_holds": sum(1 for u in queue if lamp_for_unit(u) == LAMP_YELLOW),
        "open_stops": sum(1 for u in queue if lamp_for_unit(u) == LAMP_RED),
        "hazard": hazards[0] if hazards else None,
        "rule": "赤灯は人なしで緑にしない",
        "rule_en": "False CLEAR is illegal. Red never auto-greens.",
        "footage": "Pack C aisle clip is 現場; lamps sit on the clip, not a search page.",
        "lamps": [
            {"id": LAMP_GREEN, "ja": LAMP_JA[LAMP_GREEN], "en": LAMP_EN[LAMP_GREEN], "on": line == LAMP_GREEN},
            {"id": LAMP_YELLOW, "ja": LAMP_JA[LAMP_YELLOW], "en": LAMP_EN[LAMP_YELLOW], "on": line == LAMP_YELLOW},
            {"id": LAMP_RED, "ja": LAMP_JA[LAMP_RED], "en": LAMP_EN[LAMP_RED], "on": line == LAMP_RED},
        ],
    }
