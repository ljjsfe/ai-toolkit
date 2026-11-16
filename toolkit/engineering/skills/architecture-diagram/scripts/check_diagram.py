#!/usr/bin/env python3
"""Static layout check for a generated architecture diagram (standard library only).

Usage:
  check_diagram.py <diagram.html> [...]     # exit 1 if any file has errors

Reads the first inline <svg> and checks the rules in SKILL.md that can be checked from geometry:
  - component boxes overlap each other (nesting one inside another is allowed); the 40px
    gap between rows is not measured
  - a component box or label sits outside the viewBox
  - the legend sits inside a boundary box (region, cluster, security group); the 20px
    margin below boundaries is not measured
  - connection arrows drawn after component boxes (warning: z-order)
  - template hooks missing: report-container id, export toolbar, SRI on CDN scripts
It does not render the page; a browser look is still needed for text overflow and fonts.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)
BACKING_FILL = "#0f172a"
SWATCH_MAX = 20          # legend swatches and dots are smaller than this in both directions


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float
    label: str
    order: int

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    def contains(self, o: "Box") -> bool:
        return self.x <= o.x and self.y <= o.y and self.x2 >= o.x2 and self.y2 >= o.y2

    def overlaps(self, o: "Box") -> bool:
        return self.x < o.x2 and o.x < self.x2 and self.y < o.y2 and o.y < self.y2

    def has_point(self, x: float, y: float) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2


def _num(el: ET.Element, attr: str) -> float:
    try:
        return float(el.get(attr, "0"))
    except ValueError:
        return 0.0


def _tag(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1]


def parse_svg(html: str) -> ET.Element:
    m = SVG_RE.search(html)
    if not m:
        raise ValueError("no inline <svg> found")
    text = re.sub(r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", m.group(0))
    return ET.fromstring(text)


def check(html: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        svg = parse_svg(html)
    except (ValueError, ET.ParseError) as e:
        return [f"cannot read the diagram svg: {e}"], warnings

    vb = [float(v) for v in re.split(r"[ ,]+", svg.get("viewBox", "0 0 0 0").strip())]
    view = Box(vb[0], vb[1], vb[2], vb[3], "viewBox", -1)

    elements = [el for el in svg.iter() if _tag(el) in ("rect", "line", "path", "text")]
    # label each rect by the first text drawn inside it after it
    texts = [(i, el) for i, el in enumerate(elements) if _tag(el) == "text"]
    components: list[Box] = []
    boundaries: list[Box] = []
    arrows: list[int] = []
    legend_points: list[tuple[float, float]] = []
    for i, el in enumerate(elements):
        tag = _tag(el)
        if tag == "rect":
            if el.get("width", "").endswith("%"):
                continue                                   # background grid
            b = Box(_num(el, "x"), _num(el, "y"), _num(el, "width"), _num(el, "height"), "", i)
            if el.get("fill", "").lower() == BACKING_FILL and not el.get("stroke"):
                continue                                   # opaque backing rect under a component
            if b.w < SWATCH_MAX and b.h < SWATCH_MAX:
                continue                                   # legend swatch
            label = next(("".join(t.itertext()).strip() for j, t in texts
                          if j > i and b.has_point(_num(t, "x"), _num(t, "y"))), "")
            b = Box(b.x, b.y, b.w, b.h, label or f"rect at ({b.x:g},{b.y:g})", i)
            (boundaries if el.get("stroke-dasharray") else components).append(b)
            if not view.contains(b):
                errors.append(f'"{b.label}" extends outside the viewBox {svg.get("viewBox")}; enlarge the viewBox')
        elif tag in ("line", "path") and el.get("marker-end"):
            arrows.append(i)
        elif tag == "text":
            content = "".join(el.itertext()).strip()
            x, y = _num(el, "x"), _num(el, "y")
            if content.lower() == "legend":
                legend_points.append((x, y))
            if content and not view.has_point(x, y):
                errors.append(f'text "{content[:30]}" sits outside the viewBox')

    for n, a in enumerate(components):
        for b in components[n + 1:]:
            if a.overlaps(b) and not (a.contains(b) or b.contains(a)):
                errors.append(f'"{a.label}" and "{b.label}" overlap; separate them '
                              "(this check finds overlap only; measure the 40px row gap by eye)")

    for x, y in legend_points:
        for bd in boundaries:
            if bd.has_point(x, y):
                errors.append(f'the legend at ({x:g},{y:g}) is inside the boundary "{bd.label}" '
                              f"ending at y={bd.y2:g}; move it below every boundary "
                              "(the 20px margin is not measured here)")

    first_component = min((c.order for c in components), default=None)
    late = [i for i in arrows if first_component is not None and i > first_component]
    if late:
        warnings.append(f"{len(late)} arrow(s) drawn after the first component box; draw arrows early "
                        "so boxes paint over them")

    if 'id="report-container"' not in html:
        errors.append('missing id="report-container" (the export toolbar captures this element)')
    if "toolbar-toggle" not in html:
        errors.append("missing the export toolbar from resources/template.html")
    for src in re.findall(r"<script[^>]+src=\"https?://[^\"]+\"[^>]*>", html):
        if "integrity=" not in src:
            errors.append(f"CDN script without an integrity hash: {src[:80]}")
    return errors, warnings


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    failed = False
    for name in argv:
        try:
            text = Path(name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read {name}: {e}", file=sys.stderr)
            return 2
        errors, warnings = check(text)
        for w in warnings:
            print(f"{name}: warning: {w}")
        for e in errors:
            print(f"{name}: error: {e}")
        print(f"{name}: {'OK' if not errors else f'FAILED ({len(errors)} error(s))'}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
