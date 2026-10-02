#!/usr/bin/env python3
"""Build a 16:9 slide PDF of the Scribner 安灯 andon implementation.

    python3 docs/deck/build_andon_deck.py
    # writes docs/Scribner-Andon-Implementation.pdf

ReportLab / Pillow are deck-only. Do not add them to
tools/scribner/requirements.txt (ConfigMap budget).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent / "assets"
OUT = ROOT / "docs" / "Scribner-Andon-Implementation.pdf"

W, H = 13.333 * inch, 7.5 * inch  # PowerPoint 16:9
BG = HexColor("#07090c")
PANEL = HexColor("#12181f")
PANEL2 = HexColor("#1a222c")
RULE = HexColor("#2c3a4a")
TEXT = HexColor("#e6edf3")
MUTED = HexColor("#7d93a8")
GOLD = HexColor("#f5c518")
GREEN = HexColor("#1dff7a")
YELLOW = HexColor("#ffd000")
RED = HexColor("#ff2a2a")
REDLINE_BG = HexColor("#2a1214")

_FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_CJK = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"


def _register() -> None:
    pdfmetrics.registerFont(TTFont("Sans", _FONT_SANS))
    pdfmetrics.registerFont(TTFont("SansBold", _FONT_BOLD))
    if Path(_FONT_CJK).exists():
        pdfmetrics.registerFont(TTFont("CJK", _FONT_CJK))
    else:
        pdfmetrics.registerFont(TTFont("CJK", _FONT_SANS))


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x3000 <= o <= 0x303F
        or 0x3040 <= o <= 0x30FF
        or 0x31F0 <= o <= 0x31FF
        or 0x3400 <= o <= 0x4DBF
        or 0x4E00 <= o <= 0x9FFF
        or 0xF900 <= o <= 0xFAFF
        or 0xFF00 <= o <= 0xFFEF
    )


def _runs(text: str) -> list[tuple[bool, str]]:
    if not text:
        return []
    out: list[tuple[bool, str]] = []
    cur_cjk = _is_cjk(text[0])
    buf = [text[0]]
    for ch in text[1:]:
        cjk = _is_cjk(ch)
        if cjk == cur_cjk:
            buf.append(ch)
            continue
        out.append((cur_cjk, "".join(buf)))
        buf = [ch]
        cur_cjk = cjk
    out.append((cur_cjk, "".join(buf)))
    return out


def _mixed_width(c: canvas.Canvas, text: str, size: float, bold: bool = False) -> float:
    latin = "SansBold" if bold else "Sans"
    total = 0.0
    for is_cjk, run in _runs(text):
        font = "CJK" if is_cjk else latin
        total += c.stringWidth(run, font, size)
    return total


def draw_mixed(
    c: canvas.Canvas,
    x: float,
    y: float,
    text: str,
    size: float,
    color=TEXT,
    bold: bool = False,
    align: str = "left",
) -> float:
    """Draw Latin with DejaVu and CJK with Droid. Mixed reportlab CJK strings drop Latin."""
    width = _mixed_width(c, text, size, bold=bold)
    if align == "center":
        x = x - width / 2
    elif align == "right":
        x = x - width
    c.setFillColor(color)
    cursor = x
    latin = "SansBold" if bold else "Sans"
    for is_cjk, run in _runs(text):
        font = "CJK" if is_cjk else latin
        c.setFont(font, size)
        c.drawString(cursor, y, run)
        cursor += c.stringWidth(run, font, size)
    return cursor


def _wrap(text: str, n: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if len(trial) > n:
            if cur:
                lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _crop_chrome(path: Path) -> Path:
    """Drop browser chrome / wallpaper so the operator UI fills the frame."""
    dest = Path("/tmp") / (path.stem + "-crop.png")
    im = Image.open(path).convert("RGB")
    w, h = im.size
    step = max(1, w // 320)

    def lum(x: int, y: int) -> float:
        r, g, b = im.getpixel((min(w - 1, max(0, x)), min(h - 1, max(0, y))))
        return (r + g + b) / 3.0

    def row_frac(y: int, thresh: float = 58) -> float:
        xs = range(0, w, step)
        n = 0
        dark = 0
        for x in xs:
            n += 1
            if lum(x, y) < thresh:
                dark += 1
        return dark / max(1, n)

    def col_frac(x: int, y0: int, y1: int, thresh: float = 58) -> float:
        ys = range(y0, y1, step)
        n = 0
        dark = 0
        for y in ys:
            n += 1
            if lum(x, y) < thresh:
                dark += 1
        return dark / max(1, n)

    top = 0
    for y in range(0, h // 2, step):
        if row_frac(y) > 0.62:
            top = y
            break
    bottom = h
    for y in range(h - 1, h // 2, -step):
        if row_frac(y) > 0.35:
            bottom = min(h, y + step)
            break
    right = w
    for x in range(w - 1, w // 2, -step):
        if col_frac(x, top, bottom) > 0.55:
            right = min(w, x + step * 2)
            break
    left = 0
    for x in range(0, w // 5, step):
        if col_frac(x, top, bottom) > 0.4:
            left = max(0, x - step)
            break
    if bottom - top < h * 0.45:
        top, bottom = 0, h
    if right - left < w * 0.55:
        left, right = 0, w
    im.crop((left, top, right, bottom)).save(dest)
    return dest


def _draw_bg(c: canvas.Canvas) -> None:
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#0a0e12"))
    c.rect(0, H - 0.08 * inch, W, 0.08 * inch, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 0.08 * inch, 1.4 * inch, 0.08 * inch, fill=1, stroke=0)


def _footer(c: canvas.Canvas, n: int, total: int) -> None:
    c.setFillColor(RULE)
    c.rect(0, 0, W, 0.38 * inch, fill=1, stroke=0)
    draw_mixed(
        c,
        0.45 * inch,
        0.14 * inch,
        "Scribner  安灯  ANDON  ·  Pack C  sdg_warehouse_cam-2  ·  VAST Builders Challenge",
        8,
        MUTED,
    )
    c.setFillColor(MUTED)
    c.setFont("Sans", 8)
    c.drawRightString(W - 0.45 * inch, 0.14 * inch, f"{n}  /  {total}")


def _title_bar(c: canvas.Canvas, kicker: str, title: str, sub: str = "") -> None:
    c.setFillColor(GOLD)
    c.setFont("Sans", 9)
    c.drawString(0.55 * inch, H - 0.42 * inch, kicker.upper())
    draw_mixed(c, 0.55 * inch, H - 0.78 * inch, title, 20, TEXT, bold=True)
    if sub:
        draw_mixed(c, 0.55 * inch, H - 1.05 * inch, sub, 11, MUTED)


def _card(c: canvas.Canvas, x, y, w, h, fill=PANEL) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)


def _lamp(c: canvas.Canvas, x, y, r, color, on: bool) -> None:
    c.setFillColor(HexColor("#151515"))
    c.setStrokeColor(HexColor("#222222"))
    c.circle(x, y, r, fill=1, stroke=1)
    if on:
        c.setFillColor(Color(color.red, color.green, color.blue, alpha=0.25))
        c.circle(x, y, r * 1.55, fill=1, stroke=0)
        c.setFillColor(color)
        c.circle(x, y, r, fill=1, stroke=0)


def _bullet(c: canvas.Canvas, x, y, text, size=11, color=TEXT) -> float:
    c.setFillColor(GOLD)
    c.circle(x + 4, y + 3, 2.2, fill=1, stroke=0)
    draw_mixed(c, x + 14, y, text, size, color)
    return y - 18


def _shot(c: canvas.Canvas, img: Path, x, y, w, h) -> None:
    c.setFillColor(HexColor("#050608"))
    c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
    if not img.exists():
        return
    framed = _crop_chrome(img) if img.name.startswith("ui-") else img
    im = Image.open(framed)
    iw, ih = im.size
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    ox = x + (w - dw) / 2
    oy = y + (h - dh) / 2
    c.drawImage(str(framed), ox, oy, width=dw, height=dh, preserveAspectRatio=True, mask="auto")


def slide_title(c: canvas.Canvas) -> None:
    _draw_bg(c)
    c.setFillColor(GOLD)
    c.setFont("Sans", 11)
    c.drawString(0.7 * inch, H - 1.5 * inch, "VAST BUILDERS CHALLENGE  ·  PRIMARY")
    draw_mixed(c, 0.7 * inch, H - 2.25 * inch, "Scribner  安灯", 36, TEXT, bold=True)
    c.setFont("SansBold", 28)
    c.setFillColor(GOLD)
    c.drawString(0.7 * inch, H - 2.75 * inch, "ANDON")
    draw_mixed(
        c,
        0.7 * inch,
        H - 3.25 * inch,
        "Japanese QC visual control on official Pack C warehouse video",
        14,
        MUTED,
    )
    for i, (col, ja, en, on) in enumerate(
        [
            (GREEN, "正常", "CLEAR / run", False),
            (YELLOW, "呼び出し", "HOLD / call", False),
            (RED, "停止", "ALERT / stop", True),
        ]
    ):
        x = 0.95 * inch + i * 1.55 * inch
        _lamp(c, x, 2.55 * inch, 22, col, on)
        draw_mixed(c, x, 2.05 * inch, ja, 11, TEXT, align="center")
        c.setFillColor(MUTED)
        c.setFont("Sans", 8)
        c.drawCentredString(x, 1.85 * inch, en)
    draw_mixed(c, 0.7 * inch, 1.15 * inch, "person close to a moving vehicle", 12, TEXT)
    draw_mixed(
        c,
        0.7 * inch,
        0.9 * inch,
        "sdg_warehouse_cam-2  ·  warehouse3  ·  jidoka / poka-yoke / mieruka",
        10,
        MUTED,
    )
    draw_mixed(
        c,
        W - 0.55 * inch,
        0.9 * inch,
        "VAST  ·  NVIDIA Cosmos  ·  CoreWeave / W&B  ·  Cursor",
        9,
        MUTED,
        align="right",
    )


def slide_problem(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "01  Problem",
        "A near-miss is still a human scrubbing cameras",
        "The Architecture Reference payoff is already indexed. The product is stopping the line.",
    )
    items = [
        ("The brief’s commodity example is PPE / hard-hat.", "We do not build that. Judges have seen it."),
        ("Pack C is already segmented and searchable.", "Re-ingest. Do not re-upload. Do not film LEGO for the judged demo."),
        ("VSS Explore is the platform UI.", "Reskinning search is not a product. Andon + jidoka is."),
        ("A person close to a moving vehicle is the official query.", "The gate must fail closed. False CLEAR is 重大不良."),
    ]
    y = H - 1.55 * inch
    for head, body in items:
        _card(c, 0.5 * inch, y - 0.95 * inch, W - 1.0 * inch, 0.9 * inch)
        draw_mixed(c, 0.72 * inch, y - 0.35 * inch, head, 12, GOLD, bold=True)
        draw_mixed(c, 0.72 * inch, y - 0.62 * inch, body, 11, MUTED)
        y -= 1.08 * inch


def slide_product(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "02  Product",
        "安灯 on the Pack C clip — the clip is 現場",
        "Green means the aisle is clear. Yellow calls a human. Red is a near-miss. The line does not run until someone looks.",
    )
    triples = [
        (GREEN, "緑  正常", "AUTO_CLEAR", "Path looks clear. HIGH confidence. Line runs."),
        (YELLOW, "黄  呼び出し", "HOLD", "Andon cord. Glare, far-side, UNCLEAR. A human looks."),
        (RED, "赤  停止", "AUTO_ALERT", "Near-miss or blocked path. Do not auto-clear."),
    ]
    for i, (col, ja, en, body) in enumerate(triples):
        x = 0.5 * inch + i * 4.2 * inch
        _card(c, x, 1.35 * inch, 4.0 * inch, 4.35 * inch)
        _lamp(c, x + 2.0 * inch, 4.85 * inch, 28, col, True)
        draw_mixed(c, x + 2.0 * inch, 4.2 * inch, ja, 16, TEXT, align="center")
        c.setFillColor(col)
        c.setFont("SansBold", 11)
        c.drawCentredString(x + 2.0 * inch, 3.9 * inch, en)
        textobject = c.beginText(x + 0.28 * inch, 3.4 * inch)
        textobject.setFont("Sans", 10)
        textobject.setFillColor(MUTED)
        for line in _wrap(body, 32):
            textobject.textLine(line)
        c.drawText(textobject)
        draw_mixed(
            c,
            x + 2.0 * inch,
            1.6 * inch,
            "O pulls the cord (UNSAFE)   A/C = 正常 CLEAR",
            8,
            MUTED,
            align="center",
        )


def slide_tps(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "03  Toyota Production System",
        "Not a translation sticker — the mapping is the product",
        "jidoka 自働化  ·  poka-yoke ポカヨケ  ·  mieruka 見える化  ·  gemba 現場",
    )
    rows = [
        ("現場 gemba", "The Pack C aisle clip", "sdg_warehouse_cam-2 / warehouse3"),
        ("安灯 andon", "Three lamps over that clip", "Line = worst open ticket. Station = this clip."),
        ("自働化 jidoka", "Automation with a human touch", "AUTO_* only when the caption is confident."),
        ("ポカヨケ poka-yoke", "Fool-proof the red line", "gate_ok on HOLD is 400. 赤 never auto-greens."),
        ("見える化 mieruka", "Make the risk visible", "/api/andon, sticky lamps, shift report."),
        ("重大不良", "False CLEAR", "A red lamp does not become green without a person."),
    ]
    y = H - 1.45 * inch
    for a, b, d in rows:
        _card(c, 0.5 * inch, y - 0.72 * inch, W - 1.0 * inch, 0.68 * inch)
        draw_mixed(c, 0.7 * inch, y - 0.32 * inch, a, 12, GOLD, bold=True)
        draw_mixed(c, 3.6 * inch, y - 0.32 * inch, b, 11, TEXT)
        draw_mixed(c, 8.3 * inch, y - 0.32 * inch, d, 10, MUTED)
        y -= 0.82 * inch


def slide_schema(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "04  Prompt as schema",
        "The ingest prompt decides what is searchable",
        "≤800 characters. Labeled prose. Cosmos strips JSON. Same fields are the official payoff query.",
    )
    fields = [
        "PERSON",
        "VEHICLE",
        "MOTION",
        "DISTANCE",
        "PATH_CLEAR",
        "NEAR_MISS",
        "HAZARD",
        "UNCLEAR",
        "CONFIDENCE",
    ]
    for i, f in enumerate(fields):
        col, row = i % 3, i // 3
        x = 0.5 * inch + col * 4.2 * inch
        y = H - 1.55 * inch - row * 0.58 * inch
        _card(c, x, y - 0.46 * inch, 4.0 * inch, 0.46 * inch, PANEL2)
        c.setFillColor(GOLD)
        c.setFont("SansBold", 11)
        c.drawCentredString(x + 2.0 * inch, y - 0.3 * inch, f)
    _card(c, 0.5 * inch, 1.15 * inch, W - 1.0 * inch, 3.0 * inch)
    c.setFillColor(MUTED)
    c.setFont("Sans", 9)
    c.drawString(0.72 * inch, 3.8 * inch, "EXAMPLE  ·  forklift-near-person")
    cap = (
        "PERSON: YES.  VEHICLE: forklift.  MOTION: MOVING.  DISTANCE: CLOSE.  "
        "PATH_CLEAR: NO.  NEAR_MISS: YES.  HAZARD: forklift-near-person.  "
        "UNCLEAR: NONE.  CONFIDENCE: HIGH."
    )
    t = c.beginText(0.72 * inch, 3.4 * inch)
    t.setFont("Sans", 11)
    t.setFillColor(TEXT)
    for line in _wrap(cap, 95):
        t.textLine(line)
    c.drawText(t)
    draw_mixed(
        c,
        0.72 * inch,
        2.0 * inch,
        "Gate: AUTO_ALERT / 赤 停止.  PATH_CLEAR YES + NEAR_MISS YES is inconsistent — never AUTO_CLEAR.",
        12,
        RED,
    )


def slide_stack(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "05  Official stack only",
        "Implicit identity. No PPE billboard.",
        "https://github.com/vast-data/vast-builders-challenge  ·  config.example  ·  skills, not invented curl",
    )
    boxes = [
        ("VAST", "S3  ·  DataEngine  ·  VastDB\nRe-ingest Pack C. Ingress /app."),
        ("NVIDIA", "Cosmos Reason captions\nEmbed1 256-d  ·  YOLO11 corroborates"),
        ("CoreWeave / W&B", "Optional prior via Inference\nCannot undercut NEAR_MISS"),
        ("Cursor", "Skills + this gate\nnumpy logistic, ConfigMap ≲1 MiB"),
    ]
    for i, (head, body) in enumerate(boxes):
        x = 0.5 * inch + (i % 2) * 6.35 * inch
        y = 3.55 * inch if i < 2 else 1.0 * inch
        _card(c, x, y, 6.1 * inch, 2.3 * inch)
        c.setFillColor(GOLD)
        c.setFont("SansBold", 14)
        c.drawString(x + 0.28 * inch, y + 1.8 * inch, head)
        t = c.beginText(x + 0.28 * inch, y + 1.35 * inch)
        t.setFont("Sans", 12)
        t.setFillColor(TEXT)
        for line in body.split("\n"):
            t.textLine(line)
        c.drawText(t)
    draw_mixed(
        c,
        0.55 * inch,
        0.55 * inch,
        "Never: Canary ASR  ·  docker  ·  GPU host 166.19.38.112  ·  /api/v1/reports  ·  YouTube",
        9,
        MUTED,
    )


def slide_gate(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "06  Fail-closed gate",
        "赤灯は人なしで緑にしない",
        "False CLEAR is illegal. YOLO never sole-sources AUTO_CLEAR.",
    )
    left = [
        "PATH_CLEAR YES + NEAR_MISS YES",
        "Named hazard (forklift-near-person, pallet)",
        "CONFIDENCE LOW or UNCLEAR nonempty",
        "view_blocked / occlusion (hand only, not person)",
        "YOLO person+vehicle without HIGH PATH_CLEAR",
        "W&B prior cannot pull NEAR_MISS under 0.8",
    ]
    right = [
        "POST gate_ok=true on HOLD → 400",
        "AUTO_ALERT → CLEAR needs confirm_escape",
        "Override reason cannot be agree / empty",
        "O / U pulls the andon cord (UNSAFE)",
        "A / C = 正常 CLEAR",
        "Empty queue → line lamp 緑 正常",
    ]
    _card(c, 0.5 * inch, 0.7 * inch, 6.1 * inch, 4.85 * inch)
    c.setFillColor(RED)
    c.setFont("SansBold", 12)
    c.drawString(0.75 * inch, 5.2 * inch, "Never AUTO_CLEAR")
    y = 4.8 * inch
    for item in left:
        y = _bullet(c, 0.75 * inch, y, item) - 6
    _card(c, 6.8 * inch, 0.7 * inch, 6.05 * inch, 4.85 * inch)
    c.setFillColor(GOLD)
    c.setFont("SansBold", 12)
    c.drawString(7.05 * inch, 5.2 * inch, "Poka-yoke")
    y = 4.8 * inch
    for item in right:
        y = _bullet(c, 7.05 * inch, y, item) - 6


def slide_loop(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "07  Implementation loop",
        "Caption → parse → prior → gate → human → retrain",
        "FEATURE_VERSION 3. w0[1]=1 on prior_logit. numpy only. Sibling imports for ConfigMap.",
    )
    steps = [
        ("1", "Scan", "Pack C explore\nmock 40 units"),
        ("2", "Parse", "PATH_CLEAR\nNEAR_MISS"),
        ("3", "Prior", "heuristic\n+ W&B optional"),
        ("4", "Gate", "CLEAR / ALERT\n/ HOLD + audit"),
        ("5", "Andon", "line + station\nlamps"),
        ("6", "HITL", "A/O labels\nRetrain"),
    ]
    for i, (n, head, body) in enumerate(steps):
        x = 0.45 * inch + i * 2.15 * inch
        _card(c, x, 2.55 * inch, 2.02 * inch, 2.7 * inch)
        c.setFillColor(GOLD)
        c.setFont("SansBold", 16)
        c.drawCentredString(x + 1.01 * inch, 4.85 * inch, n)
        c.setFillColor(TEXT)
        c.setFont("SansBold", 12)
        c.drawCentredString(x + 1.01 * inch, 4.5 * inch, head)
        t = c.beginText()
        t.setFont("Sans", 9)
        t.setFillColor(MUTED)
        t.setTextOrigin(x + 0.18 * inch, 4.1 * inch)
        for line in body.split("\n"):
            t.textLine(line)
        c.drawText(t)
        if i < 5:
            c.setFillColor(GOLD)
            c.setFont("SansBold", 14)
            c.drawString(x + 1.95 * inch, 3.7 * inch, ">")
    _card(c, 0.5 * inch, 0.7 * inch, W - 1.0 * inch, 1.6 * inch)
    draw_mixed(
        c,
        0.72 * inch,
        1.85 * inch,
        "Files:  andon.py  ·  gate.py  ·  inspection.py  ·  kits.py  ·  learn.py  ·  main.py  /api/andon  ·  static/index.html",
        11,
        TEXT,
    )
    draw_mixed(
        c,
        0.72 * inch,
        1.5 * inch,
        "Line lamp = worst open review ticket (red beats yellow). Station lamp = the clip on screen.",
        10,
        MUTED,
    )
    draw_mixed(
        c,
        0.72 * inch,
        1.2 * inch,
        "Live /clip streams VSS. Mock paints andon-tinted aisle footage (緑 empty · 黄 hold · 赤 near-miss).",
        10,
        MUTED,
    )
    draw_mixed(
        c,
        0.72 * inch,
        0.9 * inch,
        "Retrain logs andon_line to W&B when keyed. Coverage should rise. Unclear distance stays 黄.",
        10,
        MUTED,
    )


def slide_operator_shot(c: canvas.Canvas, kicker: str, title: str, sub: str, img: Path, caption: str) -> None:
    _draw_bg(c)
    _title_bar(c, kicker, title, sub)
    _shot(c, img, 0.45 * inch, 0.5 * inch, W - 0.9 * inch, 5.2 * inch)
    draw_mixed(c, W / 2, 0.42 * inch, caption, 8, MUTED, align="center")


def slide_aisles(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "09  Footage language",
        "The clip is tinted to the station lamp",
        "Live mode streams VSS Pack C. Mock mode is an aisle stand-in — never a grey rectangle.",
    )
    files = [
        (ASSETS / "aisle-green.png", "緑  正常", "PATH CLEAR", GREEN),
        (ASSETS / "aisle-yellow.png", "黄  呼び出し", "HOLD", YELLOW),
        (ASSETS / "aisle-red.png", "赤  停止", "NEAR MISS", RED),
    ]
    for i, (p, ja, en, col) in enumerate(files):
        x = 0.45 * inch + i * 4.25 * inch
        _card(c, x, 0.7 * inch, 4.1 * inch, 4.85 * inch)
        if p.exists():
            c.drawImage(
                str(p),
                x + 0.15 * inch,
                1.55 * inch,
                width=3.8 * inch,
                height=3.05 * inch,
                preserveAspectRatio=True,
                mask="auto",
            )
        draw_mixed(c, x + 2.05 * inch, 1.2 * inch, ja, 13, col, align="center")
        c.setFillColor(MUTED)
        c.setFont("Sans", 9)
        c.drawCentredString(x + 2.05 * inch, 0.92 * inch, en)


def slide_two_up(
    c: canvas.Canvas,
    kicker: str,
    title: str,
    sub: str,
    left: Path,
    right: Path,
    left_cap: str,
    right_cap: str,
) -> None:
    _draw_bg(c)
    _title_bar(c, kicker, title, sub)
    _shot(c, left, 0.35 * inch, 0.5 * inch, 6.25 * inch, 5.15 * inch)
    _shot(c, right, 6.73 * inch, 0.5 * inch, 6.25 * inch, 5.15 * inch)
    draw_mixed(c, 3.47 * inch, 0.42 * inch, left_cap, 8, MUTED, align="center")
    draw_mixed(c, 9.85 * inch, 0.42 * inch, right_cap, 8, MUTED, align="center")


def slide_demo(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "12  Two-minute demo",
        "Show the lamps, then the labels, then the stack",
        "Operator keys: A/C 正常 CLEAR · O/U 異常 cord · N next",
    )
    steps = [
        ("1", "Problem", "A person close to a moving vehicle is still someone scrubbing cameras."),
        ("2", "Andon", "緑 AUTO_CLEAR · 黄 HOLD · 赤 AUTO_ALERT. Station ≠ line on purpose."),
        ("3", "Schema", "PATH_CLEAR YES vs NEAR_MISS YES. Prompt is the schema."),
        ("4", "HITL", "Label ~15 HOLDs. Retrain. Coverage up. HOLD band narrows."),
        ("5", "Red line", "Unclear-distance stays 黄. 赤灯は人なしで緑にしない."),
        ("6", "Name it", "Pack C camera + footer: VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor."),
    ]
    y = H - 1.5 * inch
    for n, head, body in steps:
        _card(c, 0.5 * inch, y - 0.72 * inch, W - 1.0 * inch, 0.68 * inch)
        c.setFillColor(GOLD)
        c.setFont("SansBold", 16)
        c.drawString(0.72 * inch, y - 0.42 * inch, n)
        c.setFillColor(TEXT)
        c.setFont("SansBold", 12)
        c.drawString(1.25 * inch, y - 0.32 * inch, head)
        draw_mixed(c, 2.6 * inch, y - 0.32 * inch, body, 11, MUTED)
        y -= 0.82 * inch


def slide_never(c: canvas.Canvas) -> None:
    _draw_bg(c)
    _title_bar(
        c,
        "13  Spec lock",
        "vast-builders-challenge is the source, the guideline, and the spec",
        "config.example env names  ·  retrieval/ingest/gpu skills  ·  deploy-app-no-registry  ·  /app",
    )
    never = [
        "Do not build a hard-hat / PPE detector.",
        "Do not reskin VSS Explore. This is andon, not search.",
        "Do not ingest YouTube or internet video.",
        "Do not Docker. Do not rebuild DataEngine.",
        "Do not wire Canary. Do not hardcode 166.19.38.112.",
        "Do not invent VSS routes (/reports, /alerts, /videos/ask).",
        "Do not mix Plan B LEGO BOMs onto this branch.",
        "Do not claim live Pack C if you only ran mock ffmpeg clips.",
        "Do not AUTO_CLEAR from YOLO person+vehicle alone.",
        "Do not ship localhost as the judged demo — Ingress path is /app.",
    ]
    y = H - 1.5 * inch
    for i, item in enumerate(never):
        col = 0 if i < 5 else 1
        row = i if i < 5 else i - 5
        x = 0.5 * inch + col * 6.4 * inch
        yy = y - row * 0.85 * inch
        _card(c, x, yy - 0.72 * inch, 6.2 * inch, 0.75 * inch, REDLINE_BG if i in {0, 7, 8, 9} else PANEL)
        draw_mixed(c, x + 0.22 * inch, yy - 0.42 * inch, item, 11, TEXT)


def slide_close(c: canvas.Canvas) -> None:
    _draw_bg(c)
    c.setFillColor(GOLD)
    c.setFont("Sans", 11)
    c.drawString(0.7 * inch, H - 1.4 * inch, "ASK")
    draw_mixed(c, 0.7 * inch, H - 2.15 * inch, "Re-ingest Pack C. Put the andon on /app.", 26, TEXT, bold=True)
    draw_mixed(
        c,
        0.7 * inch,
        H - 2.55 * inch,
        "Workshop VM  ·  ingest-kits / ingest-warehouse  ·  deploy-scribner",
        13,
        MUTED,
    )
    draw_mixed(c, 0.7 * inch, H - 2.9 * inch, "赤灯は人なしで緑にしない", 11, MUTED)
    remaining = [
        ("Now", "Operator UI on mock. 64 adversarial tests. False CLEAR closed."),
        ("Cowork laptop", "GitHub.com mirror. Smoke every logged-in stack tool."),
        ("Event VM", "Re-ingest sdg_warehouse_cam-2. Deploy Ingress /app."),
        ("Judges", "Green aisle. Yellow call. Red near-miss. A human pulls the cord."),
    ]
    y = 3.7 * inch
    for head, body in remaining:
        _card(c, 0.55 * inch, y - 0.7 * inch, W - 1.1 * inch, 0.65 * inch)
        draw_mixed(c, 0.78 * inch, y - 0.4 * inch, head, 11, GOLD, bold=True)
        draw_mixed(c, 3.1 * inch, y - 0.4 * inch, body, 11, TEXT)
        y -= 0.78 * inch


def build() -> Path:
    _register()
    ASSETS.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    slides: list[tuple] = []

    def add(fn, *args):
        slides.append((fn, args))

    add(slide_title)
    add(slide_problem)
    add(slide_product)
    add(slide_tps)
    add(slide_schema)
    add(slide_stack)
    add(slide_gate)
    add(slide_loop)
    add(
        slide_operator_shot,
        "08  Operator  ·  HOLD",
        "Line 停止, station 呼び出し — the clip is the aisle",
        "Worst open ticket is red. This unit is a yellow call. That split is the board.",
        ASSETS / "ui-hold.png",
        "Mock operator UI  ·  Pack C stand-in  ·  sticky 安灯  ·  O pulls the andon cord",
    )
    add(slide_aisles)
    add(
        slide_two_up,
        "10  Station lamps",
        "Station 正常 vs station 停止 — line can stay red",
        "AUTO_CLEAR is a green frame on this clip. AUTO_ALERT is a red near-miss. False CLEAR needs confirm_escape.",
        ASSETS / "ui-clear.png",
        ASSETS / "ui-alert.png",
        "wh-006  ·  AUTO_CLEAR  ·  緑 正常  ·  PATH_CLEAR",
        "wh-029  ·  AUTO_ALERT  ·  赤 停止  ·  pallet-in-walkway  ·  p_fail 0.88",
    )
    add(
        slide_two_up,
        "11  Surfaces",
        "All units and the shift report share the same LINE",
        "Line lamp = worst open review ticket. Report uses review_queue so LINE matches /api/andon.",
        ASSETS / "ui-units.png",
        ASSETS / "ui-report.png",
        "All units  ·  green / yellow / red by gate",
        "Shift report  ·  安灯 line  ·  false CLEAR is illegal",
    )
    add(slide_demo)
    add(slide_never)
    add(slide_close)

    total = len(slides)
    for i, (fn, args) in enumerate(slides, start=1):
        fn(c, *args)
        _footer(c, i, total)
        c.showPage()
    c.save()
    return OUT


if __name__ == "__main__":
    path = build()
    print(path, path.stat().st_size)
