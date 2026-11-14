#!/usr/bin/env python3
"""Measure a writer's voice as ranges, per language, and check a draft against them.

Usage:
  voice_metrics.py CORPUS_DIR                 # profile: per-language ranges across documents
  voice_metrics.py CORPUS_DIR --draft D.md    # also flag where the draft leaves the range
  voice_metrics.py CORPUS_DIR --json          # machine-readable profile

Reads .md and .txt files under CORPUS_DIR (recursively). Each document is measured on its own
and tagged zh or en by which script dominates; the profile reports, per language, the min /
median / max of each metric across documents — ranges, not averages, and never blended
across languages. Length units: Chinese counts CJK characters plus Latin words; English
counts words.

Metrics per document:
  sentences, mean_len, cv (sentence-length spread = stdev / mean; flat AI prose runs low),
  short_ratio (zh <= 8 chars, en <= 6 words), long_ratio (zh >= 50 chars, en >= 30 words),
  para_mean (units per paragraph),
  per 1,000 units: dash, paren, colon, semicolon, exclaim, question, risky (stock AI phrases
  from the lists below), contrast ("not X but Y" / 不是…而是), nominal (zh 进行了/使得/得以…;
  en -tion/-ment/-ness/-ity/-ance/-ence words).
Sentences: zh splits on 。！？!?… and on every line break (a single newline ends a sentence in
Chinese posts); en splits after . ! ? followed by space, except after common abbreviations
(Dr., Mr., e.g., i.e., etc., vs. ...), and on blank lines.
Draft check: a metric is flagged only beyond the corpus range widened by one interquartile
range on each side ([min − IQR, max + IQR]), because with 3–10 documents the bare [min, max]
is narrow enough that the writer's own next piece falls outside it. cv below 0.6 × the corpus
minimum is the most reliable AI-flavour tell. A stock phrase is flagged only when its rate in
the draft (per 1,000 units) is above the highest rate the writer used it at in any corpus
document; a phrase the writer never used is flagged at any rate. Fewer than 3 corpus documents
in that language: the range is printed but flagged as too thin to judge against.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

CJK = "一-鿿"
RISKY_ZH = [
    "值得注意的是", "值得一提的是", "总而言之", "综上所述", "总的来说", "某种程度上",
    "归根结底", "与此同时", "除此之外", "不仅仅是", "让我们", "我们不妨", "赋能", "抓手",
    "闭环", "颗粒度", "底层逻辑", "重新定义", "未来已来", "深刻地", "极大地", "重塑",
]
RISKY_EN = [
    "delve", "pivotal", "underscore", "tapestry", "testament", "landscape", "moreover",
    "furthermore", "crucial", "seamless", "leverage", "robust", "game-changer", "unlock",
    "it's worth noting", "it is worth noting", "in conclusion", "in today's", "navigate the",
    "ever-evolving", "foster", "showcase", "realm", "holistic",
]
NOMINAL_ZH = ["进行了", "使得", "得以", "的存在", "具有很强", "加以"]
NOMINAL_EN = re.compile(r"\b[a-z]{3,}(?:tion|ment|ness|ity|ance|ence)s?\b", re.I)
ABBREV_EN = ("dr.", "mr.", "mrs.", "ms.", "prof.", "st.", "jr.", "sr.", "vs.", "etc.", "e.g.",
             "i.e.", "cf.", "approx.", "inc.", "ltd.", "no.", "fig.")
CONTRAST_ZH = re.compile(r"不是[^。！？\n]{1,20}?(?:而是|，是)")
CONTRAST_EN = re.compile(r"\bnot\s+(?:just\s+|only\s+|merely\s+)?[^.;!?\n]{1,40}?,?\s+but\b", re.I)
PUNCT = {
    "dash": re.compile(r"——|—|–| - "),
    "paren": re.compile(r"[（(]"),
    "colon": re.compile(r"[:：]"),
    "semicolon": re.compile(r"[;；]"),
    "exclaim": re.compile(r"[!！]"),
    "question": re.compile(r"[?？]"),
}
METRICS = ["mean_len", "cv", "short_ratio", "long_ratio", "para_mean", *PUNCT, "risky",
           "contrast", "nominal"]


def strip_markup(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+", "", text, flags=re.M)
    return text.replace("**", "").replace("__", "")


def units(text: str, lang: str) -> int:
    words = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text))
    if lang == "zh":
        return len(re.findall(f"[{CJK}]", text)) + words
    return words


def language(text: str) -> str:
    cjk = len(re.findall(f"[{CJK}]", text))
    words = len(re.findall(r"[A-Za-z]+", text))
    return "zh" if cjk >= words else "en"


def sentences(text: str, lang: str) -> list[str]:
    if lang == "zh":
        parts = re.split(r"[。！？!?…]+|\n", text)
    else:
        parts = []
        for para in re.split(r"\n\s*\n", text):
            for piece in re.split(r"(?<=[.!?])\s+", para):
                prev = parts[-1].split()[-1].lower() if parts and parts[-1].split() else ""
                if prev in ABBREV_EN:
                    parts[-1] = parts[-1] + " " + piece
                else:
                    parts.append(piece)
            parts.append("")  # paragraph boundary: never merge across it
    return [p.strip() for p in parts if p.strip() and units(p, lang) > 0]


def per_k(count: int, total: int) -> float:
    return 1000.0 * count / total if total else 0.0


def doc_metrics(raw: str) -> dict:
    text = strip_markup(raw)
    lang = language(text)
    sents = sentences(text, lang)
    lens = [units(s, lang) for s in sents]
    total = units(text, lang)
    short_max, long_min = (8, 50) if lang == "zh" else (6, 30)
    mean = statistics.fmean(lens) if lens else 0.0
    cv = statistics.pstdev(lens) / mean if len(lens) > 1 and mean else 0.0
    paras = [units(p, lang) for p in re.split(r"\n\s*\n", text) if units(p, lang) > 0]
    low = text.lower()
    hits: Counter = Counter()
    for w in (RISKY_ZH if lang == "zh" else RISKY_EN):
        c = low.count(w)
        if c:
            hits[w] += c
    if lang == "zh":
        contrast = len(CONTRAST_ZH.findall(text))
        nominal = sum(text.count(w) for w in NOMINAL_ZH)
    else:
        contrast = len(CONTRAST_EN.findall(text))
        nominal = len(NOMINAL_EN.findall(text))
    m = {
        "lang": lang,
        "units": total,
        "sentences": len(lens),
        "mean_len": mean,
        "cv": cv,
        "short_ratio": sum(1 for x in lens if x <= short_max) / len(lens) if lens else 0.0,
        "long_ratio": sum(1 for x in lens if x >= long_min) / len(lens) if lens else 0.0,
        "para_mean": statistics.fmean(paras) if paras else 0.0,
        "risky": per_k(sum(hits.values()), total),
        "contrast": per_k(contrast, total),
        "nominal": per_k(nominal, total),
        "risky_hits": dict(hits),
    }
    for name, pat in PUNCT.items():
        m[name] = per_k(len(pat.findall(text)), total)
    return m


def profile(docs: list[dict]) -> dict:
    out: dict = {}
    for lang in ("zh", "en"):
        group = [d for d in docs if d["lang"] == lang]
        if not group:
            continue
        ranges = {}
        for k in METRICS:
            vals = [d[k] for d in group]
            q1, q3 = (statistics.quantiles(vals, n=4, method="inclusive")[::2]
                      if len(vals) > 1 else (vals[0], vals[0]))
            ranges[k] = {"min": min(vals), "q1": q1, "median": statistics.median(vals), "q3": q3,
                         "max": max(vals)}
        hits: Counter = Counter()
        rate_max: dict[str, float] = {}
        for d in group:
            hits.update(d["risky_hits"])
            for w, c in d["risky_hits"].items():
                rate_max[w] = max(rate_max.get(w, 0.0), per_k(c, d["units"]))
        out[lang] = {"documents": len(group), "ranges": ranges, "risky_hits": dict(hits.most_common(15)),
                     "risky_rate_max": rate_max}
    return out


def compare(draft: dict, prof: dict) -> list[str]:
    lang = draft["lang"]
    if lang not in prof:
        return [f"no {lang} documents in the corpus: nothing to compare the draft against"]
    p = prof[lang]
    flags = []
    if p["documents"] < 3:
        flags.append(f"only {p['documents']} {lang} corpus document(s): range too thin to judge")
    for k in METRICS:
        r, v = p["ranges"][k], draft[k]
        iqr = r["q3"] - r["q1"]
        lo, hi = r["min"] - iqr, r["max"] + iqr
        span = f"corpus range {r['min']:.2f}–{r['max']:.2f} ± IQR {iqr:.2f}"
        if v < lo:
            flags.append(f"{k} {v:.2f} below {span}")
        elif v > hi:
            flags.append(f"{k} {v:.2f} above {span}")
    if draft["cv"] < 0.6 * p["ranges"]["cv"]["min"]:
        flags.append("sentence lengths far flatter than the writer's: break some up, add short ones")
    allowed = p.get("risky_rate_max", {})
    over = []
    for w, c in draft["risky_hits"].items():
        rate = per_k(c, draft["units"])
        if rate > allowed.get(w, 0.0):
            over.append(f"{w}×{c} ({rate:.1f}/1k vs writer's max {allowed.get(w, 0.0):.1f}/1k)")
    if over:
        flags.append("stock phrases above the writer's observed rate: " + ", ".join(over))
    return flags


def load(corpus: Path) -> list[dict]:
    files = sorted(p for p in corpus.rglob("*") if p.suffix in {".md", ".txt"} and not p.name.startswith("."))
    return [dict(doc_metrics(p.read_text(encoding="utf-8", errors="replace")), file=str(p)) for p in files]


def render(prof: dict) -> str:
    lines = []
    for lang, p in prof.items():
        lines.append(f"## {lang} — {p['documents']} documents (min / median / max)")
        for k in METRICS:
            r = p["ranges"][k]
            lines.append(f"- {k}: {r['min']:.2f} / {r['median']:.2f} / {r['max']:.2f}")
        if p["risky_hits"]:
            lines.append("- writer's own stock-phrase use: " + ", ".join(f"{w}×{c}" for w, c in p["risky_hits"].items()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus")
    ap.add_argument("--draft")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    corpus = Path(a.corpus)
    if not corpus.is_dir():
        print(f"not a directory: {corpus}", file=sys.stderr)
        return 2
    docs = load(corpus)
    if not docs:
        print("no .md or .txt files found", file=sys.stderr)
        return 2
    prof = profile(docs)
    print(json.dumps(prof, ensure_ascii=False, indent=1) if a.json else render(prof))
    if a.draft:
        flags = compare(doc_metrics(Path(a.draft).read_text(encoding="utf-8")), prof)
        print("\n## draft vs range")
        print("\n".join(f"- {f}" for f in flags) if flags else "- inside the writer's range on every metric")
        return 1 if flags else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
