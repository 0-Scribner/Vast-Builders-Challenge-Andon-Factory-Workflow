"""Japanese QC andon on the official Builders Challenge corpus.

TPS mapping (jidoka / mieruka / poka-yoke — not a translation sticker):

- 緑 正常   AUTO_CLEAR  — path is clear, line runs
- 黄 呼び出し HOLD      — andon cord: a human must look at the clip
- 赤 停止   AUTO_ALERT  — near-miss / blocked path; do not auto-clear

現場 (gemba) is the official camera on screen (I-24, PIE, neighborhood,
warehouse, indoor). The board is the 安灯.
False CLEAR is 重大不良: a red lamp must never become green without a human.

Live mode streams the VSS segment. Mock paints a camera-kind stand-in
tinted to the station lamp — not a grey rectangle, not YouTube.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from corpus import READY_CAMERA_IDS, clip_kind, pack_for_camera, public_corpus
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
KIND_JA = {
    "warehouse": "倉庫",
    "highway": "高速道路",
    "dashcam": "運転",
    "street": "街区",
    "indoor": "屋内",
}

_RED_DECISIONS = {"AUTO_ALERT", "AUTO_FAIL", "UNSAFE"}
_YELLOW_DECISIONS = {"HOLD"}
_GREEN_DECISIONS = {"AUTO_CLEAR", "AUTO_PASS", "CLEAR"}

_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
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


def clip_path_for_lamp(lamp: str, kind: str = "warehouse") -> Path:
    lamp = lamp if lamp in _CLIP else LAMP_YELLOW
    if kind == "warehouse":
        return Path(f"/tmp/scribner_andon_{lamp}.mp4")
    return Path(f"/tmp/scribner_andon_{kind}_{lamp}.mp4")


def _scene_draw(kind: str, spec: Dict[str, str]) -> str:
    """ffmpeg drawbox chain. Lamp tint is the andon language; geometry is the camera."""
    floor, rack, fg = spec["floor"], spec["rack"], spec["fg"]
    if kind == "highway":
        return (
            f"drawbox=x=0:y=220:w=960:h=200:color={floor}:t=fill,"
            f"drawbox=x=0:y=310:w=960:h=6:color=0xf0e6a0:t=fill,"
            f"drawbox=x=80:y=250:w=70:h=8:color=0xf0e6a0:t=fill,"
            f"drawbox=x=280:y=250:w=70:h=8:color=0xf0e6a0:t=fill,"
            f"drawbox=x=480:y=250:w=70:h=8:color=0xf0e6a0:t=fill,"
            f"drawbox=x=680:y=250:w=70:h=8:color=0xf0e6a0:t=fill,"
            f"drawbox=x=0:y=0:w=960:h=8:color={fg}:t=fill"
        )
    if kind == "dashcam":
        return (
            f"drawbox=x=0:y=0:w=960:h=220:color=0x4a6a88:t=fill,"
            f"drawbox=x=0:y=220:w=960:h=320:color={floor}:t=fill,"
            f"drawbox=x=380:y=220:w=200:h=320:color=0x3a3a3a:t=fill,"
            f"drawbox=x=470:y=220:w=8:h=320:color=0xf0e6a0:t=fill,"
            f"drawbox=x=0:y=0:w=960:h=8:color={fg}:t=fill"
        )
    if kind == "street":
        return (
            f"drawbox=x=40:y=80:w=160:h=200:color={rack}:t=fill,"
            f"drawbox=x=240:y=60:w=140:h=220:color={rack}:t=fill,"
            f"drawbox=x=760:y=90:w=160:h=190:color={rack}:t=fill,"
            f"drawbox=x=0:y=300:w=960:h=240:color={floor}:t=fill,"
            f"drawbox=x=0:y=300:w=960:h=10:color=0xc4a35a:t=fill,"
            f"drawbox=x=0:y=0:w=960:h=8:color={fg}:t=fill"
        )
    if kind == "indoor":
        return (
            f"drawbox=x=0:y=0:w=180:h=540:color={rack}:t=fill,"
            f"drawbox=x=780:y=0:w=180:h=540:color={rack}:t=fill,"
            f"drawbox=x=180:y=360:w=600:h=180:color={floor}:t=fill,"
            f"drawbox=x=470:y=360:w=10:h=180:color={fg}:t=fill,"
            f"drawbox=x=0:y=0:w=960:h=8:color={fg}:t=fill"
        )
    return (
        f"drawbox=x=0:y=400:w=960:h=140:color={floor}:t=fill,"
        f"drawbox=x=150:y=20:w=32:h=380:color={rack}:t=fill,"
        f"drawbox=x=778:y=20:w=32:h=380:color={rack}:t=fill,"
        f"drawbox=x=168:y=80:w=90:h=54:color=0xc4a35a:t=fill,"
        f"drawbox=x=702:y=140:w=76:h=48:color=0xb08a48:t=fill,"
        f"drawbox=x=474:y=400:w=12:h=140:color={fg}:t=fill,"
        f"drawbox=x=0:y=0:w=960:h=8:color={fg}:t=fill"
    )


def ensure_warehouse_clip(lamp: str) -> Path:
    """Stable Pack C path used by existing RGB tests."""
    return ensure_corpus_clip(lamp, PACK_C_CAMERA)


def ensure_corpus_clip(lamp: str, camera_id: str = "") -> Path:
    """Official-camera stand-in, tinted to the andon lamp.

    Live mode streams the real VSS segment. Mock paints the gemba so the
    board and the footage share a color language.
    """
    lamp = lamp if lamp in _CLIP else LAMP_YELLOW
    cam = camera_id or PACK_C_CAMERA
    kind = clip_kind(cam)
    path = clip_path_for_lamp(lamp, kind)
    if path.exists() and path.stat().st_size > 1000:
        return path
    spec = _CLIP[lamp]
    font = _font()
    font_opt = f"fontfile={font}:" if font else ""
    scene = _scene_draw(kind, spec)
    cam_label = cam.replace(":", "-")
    label = (
        f"{scene},"
        f"drawtext={font_opt}text='{cam_label}':"
        f"fontcolor=white:fontsize=22:x=24:y=24,"
        f"drawtext={font_opt}text='{spec['label']}':"
        f"fontcolor={spec['fg']}:fontsize=28:x=24:y=56"
    )
    y_overlay = {"highway": 268, "dashcam": 360, "street": 330, "indoor": 340}.get(kind, 348)
    cmd: List[str] = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={spec['bg']}:s=960x540:d=4.2:r=24",
    ]
    if spec["vehicle"] or kind in {"highway", "dashcam", "street"}:
        cmd += ["-f", "lavfi", "-i", "color=c=0xf5a623:s=110x42:d=4.2:r=24"]
        cmd += [
            "-filter_complex",
            f"[0:v]{label}[base];[base][1:v]overlay=x='40+t*190':y={y_overlay}:shortest=1[v]",
            "-map", "[v]",
        ]
    else:
        cmd += ["-vf", label]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "4.2",
        "-an", "-movflags", "+faststart", str(path),
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if path.exists() and path.stat().st_size > 1000:
        return path
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={spec['bg']}:s=960x540:d=2:r=12",
            "-vf", scene,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "2",
            "-an", str(path),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
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
    cam = str(station_unit.get("camera_id") or camera_id or PACK_C_CAMERA)
    loc = str(station_unit.get("location") or location or LOCATION)
    kind = clip_kind(cam)
    insp = station_unit.get("inspection") or {}
    hazards = insp.get("hazards") or insp.get("missing") or []
    corpus = public_corpus()
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
        "camera_id": cam,
        "location": loc,
        "pack": pack_for_camera(cam) if cam else pack,
        "clip_kind": kind,
        "kind_ja": KIND_JA.get(kind, kind),
        "cameras": READY_CAMERA_IDS,
        "corpus": corpus,
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
        "footage": (
            "Official challenge corpus is 現場 "
            "(I-24, PIE dashcam, neighborhood, warehouse, indoor). "
            "Lamps sit on that clip, not a search page."
        ),
        "lamps": [
            {"id": LAMP_GREEN, "ja": LAMP_JA[LAMP_GREEN], "en": LAMP_EN[LAMP_GREEN], "on": line == LAMP_GREEN},
            {"id": LAMP_YELLOW, "ja": LAMP_JA[LAMP_YELLOW], "en": LAMP_EN[LAMP_YELLOW], "on": line == LAMP_YELLOW},
            {"id": LAMP_RED, "ja": LAMP_JA[LAMP_RED], "en": LAMP_EN[LAMP_RED], "on": line == LAMP_RED},
        ],
    }
