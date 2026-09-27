"""Card covers: each repository's cover resized to card size into assets/."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .model import Catalog
from .render import cover_path

COVER_SIZE = (640, 480)


def card_image(source: Path) -> Image.Image:
    """The card-size RGB image made from a 4:3 cover. Pillow is pinned in uv.lock, so the result is repeatable."""
    with Image.open(source) as image:
        if image.width * COVER_SIZE[1] != image.height * COVER_SIZE[0]:
            raise ValueError(f"{source} is {image.size}, expected a 4:3 image")
        return image.convert("RGB").resize(COVER_SIZE, Image.Resampling.LANCZOS)


def same_pixels(card: Path, source: Path) -> bool:
    """True when the committed card cover holds exactly the pixels card_image() makes from the source."""
    with Image.open(card) as committed:
        return committed.convert("RGB").tobytes() == card_image(source).tobytes()


def refresh(catalog: Catalog, index_root: Path, repos_root: Path, overrides: dict[str, Path]) -> list[str]:
    """Rebuild assets/<id>.png from each repository cover, or from an override for a repository without one."""
    notes = []
    for service in catalog.services:
        override = overrides.get(service.id)
        if override is not None and not override.is_file():
            raise FileNotFoundError(f"{service.id}: --source {override} does not exist")
        source = override or repos_root / service.repo.local / "docs/assets/cover.png"
        target = index_root / cover_path(service)
        if not source.is_file():
            if target.is_file():
                notes.append(f"kept   {target.name}: {source} not found, earlier copy stays")
                continue
            raise FileNotFoundError(f"{service.id}: no cover at {source}; pass --source {service.id}=PATH")
        card_image(source).save(target, optimize=True)
        notes.append(f"copied {target.name} from {source.name if service.id in overrides else service.repo.name}")
    return notes
