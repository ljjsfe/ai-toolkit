#!/usr/bin/env python3
"""Tests for check_diagram.py against the shipped template and small broken diagrams."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_diagram  # noqa: E402

RESOURCES = HERE.parent / "resources"
HOOKS = ('<div id="report-container"><button class="toolbar-toggle"></button>'
         '<script src="https://cdn.jsdelivr.net/npm/x@1/x.js" integrity="sha384-x"></script>')


def page(svg_body: str, view: str = "0 0 400 300") -> str:
    return f'{HOOKS}<svg viewBox="{view}">{svg_body}</svg>'


BOX = '<rect x="{x}" y="{y}" width="100" height="60" rx="6" fill="rgba(6, 78, 59, 0.4)" stroke="#34d399"/>' \
      '<text x="{tx}" y="{ty}">{label}</text>'


def box(x: int, y: int, label: str) -> str:
    return BOX.format(x=x, y=y, tx=x + 50, ty=y + 20, label=label)


class CheckDiagramTests(unittest.TestCase):
    def test_help_and_missing_file_exit_cleanly(self) -> None:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(check_diagram.main(["--help"]), 0)
            self.assertEqual(check_diagram.main(["/no/such/diagram.html"]), 2)

    def test_shipped_files_pass(self) -> None:
        for f in [RESOURCES / "template.html", *sorted((RESOURCES / "examples").glob("*.html"))]:
            with self.subTest(file=f.name):
                errors, _ = check_diagram.check(f.read_text(encoding="utf-8"))
                self.assertEqual(errors, [])

    def test_overlap_is_an_error_but_nesting_is_not(self) -> None:
        errors, _ = check_diagram.check(page(box(10, 10, "API") + box(60, 40, "Worker")))
        self.assertTrue(any('"API" and "Worker" overlap' in e for e in errors), errors)
        self.assertFalse(any("keep at least" in e for e in errors), errors)  # gap is not measured
        nested = ('<rect x="0" y="0" width="300" height="200" rx="6" fill="none" stroke="#fb7185"/>'
                  '<text x="10" y="15">VPC</text>' + box(20, 30, "API"))
        self.assertEqual(check_diagram.check(page(nested))[0], [])

    def test_legend_inside_boundary_and_outside_viewbox(self) -> None:
        svg = ('<rect x="0" y="0" width="390" height="250" rx="12" fill="none" stroke="#fbbf24" '
               'stroke-dasharray="8,4"/><text x="10" y="15">Region</text>'
               '<text x="20" y="240">Legend</text>' + box(250, 260, "DB"))
        errors, _ = check_diagram.check(page(svg))
        joined = "\n".join(errors)
        self.assertIn("legend at (20,240) is inside the boundary", joined)
        self.assertIn('"DB" extends outside the viewBox', joined)

    def test_late_arrow_warns_and_missing_hooks_error(self) -> None:
        svg = box(10, 10, "API") + '<line x1="0" y1="0" x2="5" y2="5" marker-end="url(#arrowhead)"/>'
        errors, warnings = check_diagram.check(f'<svg viewBox="0 0 400 300">{svg}</svg>')
        self.assertTrue(any("arrow(s) drawn after" in w for w in warnings))
        self.assertTrue(any("report-container" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
