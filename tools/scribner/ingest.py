"""Poka-yoke for kit clip ingest against the official upload-video contract.

Uses only POST /api/v1/videos/upload fields from
vast-builders-challenge ingest/upload-video. Rejects YouTube/http files,
unknown kits, and prompts over the live custom_prompt_max_length (800).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set
from urllib.parse import urlparse

from builders_stack import CUSTOM_PROMPT_MAX, UPLOAD_FIELDS
from kits import kit_ids

FILENAME_RE = re.compile(
    r"^kit-(?P<kit_id>[a-z0-9-]+)_unit-(?P<n>\d{3})\.(?P<ext>mp4|mov|webm|mkv|avi)$",
    re.IGNORECASE,
)
_URLISH = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
_YOUTUBE = re.compile(r"(?:^|://)?(?:www\.)?(?:youtube\.com|youtu\.be)\b", re.IGNORECASE)
ALLOWED_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


class IngestRejected(ValueError):
    """Fail-closed ingest. Message is safe to show; contains no secrets."""


def looks_like_remote(path: str) -> bool:
    raw = (path or "").strip()
    if _YOUTUBE.search(raw):
        return True
    if _URLISH.match(raw):
        scheme = urlparse(raw).scheme.lower()
        return scheme in {"http", "https", "ftp", "s3"}
    return False


def parse_kit_filename(name: str, known: Optional[Sequence[str]] = None) -> str:
    m = FILENAME_RE.match(Path(name).name)
    if not m:
        raise IngestRejected(
            f"filename {name!r} must match kit-<kit_id>_unit-<nnn>.(mp4|mov|webm|mkv|avi)"
        )
    kit_id = m.group("kit_id")
    allowed: Set[str] = set(known if known is not None else kit_ids())
    if kit_id not in allowed:
        raise IngestRejected(f"unknown kit_id={kit_id!r}; known={sorted(allowed)}")
    return kit_id


def assert_prompt_length(prompt: str, max_len: int = CUSTOM_PROMPT_MAX) -> None:
    n = len(prompt or "")
    if n > max_len:
        raise IngestRejected(f"custom_prompt is {n} chars; VSS max is {max_len}")
    if n == 0:
        raise IngestRejected("custom_prompt is required; do not send scenario instead")


def assert_uploadable(
    path: str,
    custom_prompt: str,
    *,
    known_kits: Optional[Sequence[str]] = None,
    max_prompt: int = CUSTOM_PROMPT_MAX,
    require_filename: bool = True,
) -> str:
    if looks_like_remote(path) or _YOUTUBE.search(path or ""):
        raise IngestRejected("refusing remote/YouTube path; own footage files only")
    p = Path(path)
    if p.suffix.lower() not in ALLOWED_EXT:
        raise IngestRejected(f"extension {p.suffix!r} is not an allowed upload type")
    kit_id = ""
    if require_filename:
        kit_id = parse_kit_filename(p.name, known_kits)
    assert_prompt_length(custom_prompt, max_prompt)
    return kit_id


def filter_upload_fields(data: dict) -> dict:
    """Drop empty strings and any key not in the official multipart table."""
    allowed = set(UPLOAD_FIELDS)
    out = {}
    for k, v in data.items():
        if k not in allowed:
            continue
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        out[k] = v
    if out.get("custom_prompt"):
        out.pop("scenario", None)
    return out


def tags_for(kit_id: str, unit: str, variant: str = "unknown") -> str:
    return f"kit:{kit_id},unit:{unit},variant:{variant},scribner"


def iter_clip_files(folder: str, known: Optional[Iterable[str]] = None) -> list:
    allowed = set(known if known is not None else kit_ids())
    root = Path(folder)
    if not root.is_dir():
        raise IngestRejected(f"clip folder missing: {folder}")
    files = []
    for p in sorted(root.iterdir()):
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXT:
            continue
        parse_kit_filename(p.name, allowed)
        files.append(p)
    return files
