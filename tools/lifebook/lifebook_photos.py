"""
Downloads the export's photos once, then keeps print-ready copies in a local cache.

Cache layout (all disposable, under .tmp/lifebook/photos/):
    orig/<key>.<ext>        the file exactly as downloaded (never re-fetched)
    <key>_<size>.jpg        EXIF-rotated, RGB, longest edge <= size px
    <key>_thumb.jpg         small square-ish copy for the contact sheet

A photo that can't be downloaded or decoded is reported and left out of the book.
"""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image, ImageOps

THUMB_PX = 360


@dataclass
class Photo:
    url: str
    path: Path
    thumb: Path
    width: int
    height: int

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 1.0

    @property
    def uri(self) -> str:
        return self.path.as_uri()

    @property
    def thumb_uri(self) -> str:
        return self.thumb.as_uri()


def _key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _download(url: str, dest_dir: Path) -> Path:
    if not url.lower().startswith(("http://", "https://")) and Path(url).is_file():
        return Path(url)                                   # a local file, e.g. --cover ./me.jpg
    key = _key(url)
    for existing in dest_dir.glob(f"{key}.*"):
        if existing.stat().st_size > 0:
            return existing
    last_error = None
    for _ in range(3):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
            path = dest_dir / f"{key}{ext}"
            path.write_bytes(r.content)
            return path
        except requests.RequestException as e:
            last_error = e
    raise RuntimeError(f"download failed: {last_error}")


def _prepare(url: str, cache: Path, max_px: int) -> Photo:
    key = _key(url)
    out = cache / f"{key}_{max_px}.jpg"
    thumb = cache / f"{key}_thumb.jpg"
    if out.exists() and thumb.exists():
        with Image.open(out) as im:
            return Photo(url, out, thumb, *im.size)
    src = _download(url, cache / "orig")
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        big = im.copy()
        big.thumbnail((max_px, max_px), Image.LANCZOS)
        big.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        small = im.copy()
        small.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
        small.save(thumb, "JPEG", quality=78, optimize=True)
        return Photo(url, out, thumb, *big.size)


def fetch_photos(urls: list[str], cache: Path, max_px: int = 1400, workers: int = 8,
                 log=print) -> dict[str, Photo]:
    """Returns url -> Photo for every photo that could be fetched and decoded."""
    (cache / "orig").mkdir(parents=True, exist_ok=True)
    unique = list(dict.fromkeys(u for u in urls if u))
    photos: dict[str, Photo] = {}
    failures: list[tuple[str, str]] = []

    def work(url):
        try:
            return url, _prepare(url, cache, max_px), None
        except Exception as e:  # one bad photo shouldn't stop the book
            return url, None, str(e)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for url, photo, err in pool.map(work, unique):
            done += 1
            if photo:
                photos[url] = photo
            else:
                failures.append((url, err))
            if done % 25 == 0 or done == len(unique):
                log(f"  photos {done}/{len(unique)}")
    for url, err in failures:
        log(f"  ! skipped photo ({err}): {url}")
    return photos
