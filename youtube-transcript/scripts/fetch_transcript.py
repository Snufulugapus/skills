#!/usr/bin/env python3
"""Fetch a YouTube video/Short transcript via yt-dlp and print clean text."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure_yt_dlp() -> None:
    """Install yt-dlp on demand if it isn't importable."""
    try:
        import yt_dlp  # noqa: F401
        return
    except ImportError:
        pass
    print("yt-dlp not found — installing via pip...", file=sys.stderr)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"],
        check=True,
    )


def parse_vtt(vtt_path: Path, keep_timestamps: bool) -> str:
    """Turn a VTT caption file into deduplicated plain text.

    YouTube's auto-generated VTT has rolling cues — each new cue repeats
    the tail of the previous cue with one more word. Naive concatenation
    produces massive duplication. We dedupe by exact line match in order.
    """
    ts_re = re.compile(r"^(\d\d:\d\d:\d\d)\.\d{3}\s+-->")
    tag_re = re.compile(r"<[^>]+>")
    skip_prefixes = ("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE", "X-TIMESTAMP")

    out: list[str] = []
    seen: set[str] = set()
    current_ts: str | None = None

    for raw in vtt_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(skip_prefixes):
            continue
        m = ts_re.match(line)
        if m:
            current_ts = m.group(1)
            continue
        cleaned = tag_re.sub("", line).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        if keep_timestamps and current_ts:
            out.append(f"[{current_ts}] {cleaned}")
        else:
            out.append(cleaned)
    return "\n".join(out)


def read_info(tmp_path: Path) -> dict:
    info_files = list(tmp_path.glob("*.info.json"))
    if not info_files:
        return {}
    try:
        return json.loads(info_files[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def format_duration(seconds: float | int | None) -> str:
    if not seconds:
        return "?"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def fetch(url: str, lang: str, keep_timestamps: bool) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs",
            "--write-subs",
            "--write-info-json",
            "--skip-download",
            "--sub-langs", lang,
            "--sub-format", "vtt",
            "-o", str(tmp_path / "%(id)s.%(ext)s"),
            "--no-warnings",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"yt-dlp failed (exit {result.returncode}):\n{result.stderr.strip()}"
            )

        vtt_files = [p for p in tmp_path.glob("*.vtt")]
        if not vtt_files:
            raise RuntimeError(
                f"No captions found for {url}. The video may have captions disabled, "
                f"or language '{lang}' isn't available. Try --lang with another code."
            )

        # Prefer manual subs over auto-subs if both exist
        manual = [p for p in vtt_files if ".auto." not in p.name and "-orig" not in p.name]
        vtt = manual[0] if manual else vtt_files[0]

        transcript = parse_vtt(vtt, keep_timestamps)
        info = read_info(tmp_path)

        header_lines = []
        if info:
            title = info.get("title", "")
            uploader = info.get("uploader") or info.get("channel") or ""
            duration = format_duration(info.get("duration"))
            video_id = info.get("id", "")
            header_lines.append(f"# {title}" if title else "# YouTube transcript")
            meta_bits = [b for b in (uploader, duration, video_id) if b]
            if meta_bits:
                header_lines.append(" · ".join(meta_bits))
            header_lines.append("")

        return "\n".join(header_lines) + transcript


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url", help="YouTube video, Short, or video ID")
    p.add_argument("--lang", default="en", help="Caption language code (default: en)")
    p.add_argument(
        "--timestamps", action="store_true",
        help="Prepend [HH:MM:SS] to each line",
    )
    args = p.parse_args()

    # Windows consoles default to cp1252 and mangle non-ASCII metadata/captions.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    ensure_yt_dlp()
    try:
        print(fetch(args.url, args.lang, args.timestamps))
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
