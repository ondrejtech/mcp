"""Email templates: plain-text files with $placeholder substitution."""

from __future__ import annotations

from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.txt"))


def render_template(name: str, variables: dict[str, str] | None = None) -> str:
    path = TEMPLATES_DIR / f"{name}.txt"
    if not path.exists():
        available = ", ".join(list_templates()) or "(none)"
        raise ValueError(f"Unknown template '{name}'. Available templates: {available}")
    return Template(path.read_text(encoding="utf-8")).safe_substitute(variables or {})
