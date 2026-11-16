#!/usr/bin/env python3
"""Tests for voice_metrics.py. Expected values counted by hand:

EN "I shipped it. Then the build broke at 3am on a Sunday and nobody noticed until Monday."
  sentence 1: I shipped it = 3 words; sentence 2: Then the build broke at 3am on a Sunday and
  nobody noticed until Monday = 14 words; total 17
  mean 8.5; population stdev = |14 − 3| / 2 = 5.5; cv = 5.5 / 8.5 = 0.64706
  short (<= 6 words) 1 of 2 = 0.5; long (>= 30) 0
ZH "我改了。这个功能上线以后用户少了三成！"
  3 and 14 CJK characters; total 17; same mean 8.5 and cv 0.64706; short (<= 8) 0.5
  exclaim: 1 per 17 units = 1000/17 = 58.82 per 1,000
EN "Moreover, this is crucial." 4 words, 2 stock phrases -> risky 500 per 1,000
EN "It is not a bug, but a feature." 8 words, one contrast -> 125 per 1,000
ZH "这不是技术问题，而是组织问题。" one contrast
ZH "第一行没有标点\n第二行也没有" -> 2 sentences (single newline ends a zh sentence)
EN "Dr. Smith met Mr. Lee, e.g. at noon. Then he left." -> 2 sentences, not 5
IQR widening: corpus values 1, 2, 3 -> q1 1.5, q3 2.5, IQR 1; allowed [0, 4]: 3.9 passes, 4.1 fails
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_metrics as vm  # noqa: E402

EN = "I shipped it. Then the build broke at 3am on a Sunday and nobody noticed until Monday."
ZH = "我改了。这个功能上线以后用户少了三成！"


class DocMetricTests(unittest.TestCase):
    def test_english_lengths(self) -> None:
        m = vm.doc_metrics(EN)
        self.assertEqual(m["lang"], "en")
        self.assertEqual((m["sentences"], m["units"]), (2, 17))
        self.assertAlmostEqual(m["mean_len"], 8.5)
        self.assertAlmostEqual(m["cv"], 5.5 / 8.5)
        self.assertAlmostEqual(m["short_ratio"], 0.5)
        self.assertEqual(m["long_ratio"], 0.0)

    def test_chinese_lengths_and_punct(self) -> None:
        m = vm.doc_metrics(ZH)
        self.assertEqual(m["lang"], "zh")
        self.assertEqual((m["sentences"], m["units"]), (2, 17))
        self.assertAlmostEqual(m["cv"], 5.5 / 8.5)
        self.assertAlmostEqual(m["short_ratio"], 0.5)
        self.assertAlmostEqual(m["exclaim"], 1000 / 17)

    def test_risky_and_contrast(self) -> None:
        r = vm.doc_metrics("Moreover, this is crucial.")
        self.assertAlmostEqual(r["risky"], 500.0)
        self.assertEqual(r["risky_hits"], {"moreover": 1, "crucial": 1})
        self.assertAlmostEqual(vm.doc_metrics("It is not a bug, but a feature.")["contrast"], 125.0)
        self.assertGreater(vm.doc_metrics("这不是技术问题，而是组织问题。")["contrast"], 0)

    def test_zh_single_newline_ends_sentence(self) -> None:
        self.assertEqual(vm.sentences("第一行没有标点\n第二行也没有", "zh"), ["第一行没有标点", "第二行也没有"])

    def test_en_abbreviations_do_not_split(self) -> None:
        got = vm.sentences("Dr. Smith met Mr. Lee, e.g. at noon. Then he left.", "en")
        self.assertEqual(got, ["Dr. Smith met Mr. Lee, e.g. at noon.", "Then he left."])
        self.assertEqual(len(vm.sentences("We stopped.\n\nDr.\n\nNext one.", "en")), 3)

    def test_markup_stripped(self) -> None:
        m = vm.doc_metrics("# Title\n\n```\ncode here is long long long\n```\n\n" + EN)
        self.assertEqual(m["units"], 17 + 1)  # heading word "Title" stays as its own paragraph


def fake_doc(value: float, hits: dict | None = None, units: int = 1000) -> dict:
    d = {k: value for k in vm.METRICS}
    d.update(lang="en", units=units, risky_hits=hits or {})
    return d


class ProfileTests(unittest.TestCase):
    def test_flags_only_beyond_iqr_widened_range(self) -> None:
        prof = vm.profile([fake_doc(1.0), fake_doc(2.0), fake_doc(3.0)])
        self.assertEqual(vm.compare(fake_doc(3.9), prof), [])  # outside [1, 3], inside ± IQR
        flags = vm.compare(fake_doc(4.1), prof)
        self.assertTrue(any(f.startswith("mean_len 4.10 above") for f in flags), flags)

    def test_stock_phrase_allowed_up_to_writer_rate(self) -> None:
        corpus = [fake_doc(2.0, {"robust": 2}), fake_doc(2.0), fake_doc(2.0)]
        prof = vm.profile(corpus)  # writer's max: 2 per 1,000 units
        self.assertEqual(vm.compare(fake_doc(2.0, {"robust": 2}), prof), [])
        flags = vm.compare(fake_doc(2.0, {"robust": 3, "delve": 1}), prof)
        self.assertTrue(any("robust×3" in f and "delve×1" in f for f in flags), flags)


    def test_ranges_split_by_language_and_draft_flags(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i in range(3):
                (root / f"en{i}.md").write_text(EN + "\n\nShort one. " + "word " * (5 + i) + ".",
                                                encoding="utf-8")
            (root / "zh.md").write_text(ZH, encoding="utf-8")
            prof = vm.profile(vm.load(root))
            self.assertEqual(prof["en"]["documents"], 3)
            self.assertEqual(prof["zh"]["documents"], 1)
            flat = "This is a crucial tool. This is a robust tool. This is a seamless tool."
            flags = vm.compare(vm.doc_metrics(flat), prof)
            self.assertTrue(any(f.startswith("cv ") and "below" in f for f in flags), flags)
            self.assertTrue(any("far flatter" in f for f in flags), flags)
            self.assertTrue(any("crucial×1" in f for f in flags), flags)
            zh_flags = vm.compare(vm.doc_metrics(ZH), prof)
            self.assertTrue(any("too thin" in f for f in zh_flags))

    def test_cli_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "corpus"
            root.mkdir()
            for i in range(3):
                (root / f"{i}.md").write_text(EN, encoding="utf-8")
            draft = Path(d) / "draft.md"
            draft.write_text(EN, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(vm.main([str(root), "--draft", str(draft)]), 0)
            draft.write_text("Moreover, we delve. Moreover, we delve. Moreover, we delve.", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(vm.main([str(root), "--draft", str(draft)]), 1)
            self.assertIn("draft vs range", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
