"""Summary statistics for the per-sample OCR ground truth (Table 1).

Reads every ground_truth_per_sample/template_X_sample_Y.txt and computes, per
document, a set of size/complexity metrics. It then reports Mean (SD) and
Median [Q1, Q3] for each metric, both overall and stratified by template.

Metrics per document
---------------------
- words         : whitespace-separated tokens (the primary size measure)
- unique_words  : distinct case-folded tokens (lexical diversity)
- chars         : characters including whitespace
- chars_nospace : characters excluding whitespace
- lines         : non-empty lines (a proxy for layout density)
- digits        : digit characters (clinical docs are numeric-heavy; also an
                  OCR-difficulty signal since digits lack language-model context)

Outputs
-------
- <out>/table1_per_template.csv  : one row per template (+ Overall) with the
                                   formatted "Mean (SD)" and "Median [Q1, Q3]"
                                   strings, ready to paste into the manuscript.
- <out>/summary_per_document.csv : the raw per-document metrics (long form) so
                                    you can recompute or plot anything else.
- a Markdown Table 1 printed to stdout.

An optional document-type mapping (template -> "Progress note", etc.) can be
supplied with --types pointing at a CSV with columns `template,doc_type`. When
given, a `doc_type` column is added to the per-template table.

Usage
-----
    python scripts/summarize_ground_truth.py
    python scripts/summarize_ground_truth.py --types docs/template_types.csv
"""

import argparse
import os
import re

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
PER_SAMPLE_DIR = os.path.join(BASE, "ground_truth_per_sample")

# Matches "template_<int>_sample_<int>.txt".
NAME_RE = re.compile(r"^template_(\d+)_sample_(\d+)\.txt$")

# Metric name -> column header used in the printed/CSV tables.
METRICS = {
    "words": "Words",
    "unique_words": "Unique words",
    "chars": "Characters",
    "chars_nospace": "Characters (no space)",
    "lines": "Lines",
    "digits": "Digits",
}


def document_metrics(text: str) -> dict:
    """Compute all per-document metrics for a single ground-truth string."""
    tokens = text.split()
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return {
        "words": len(tokens),
        "unique_words": len({t.lower() for t in tokens}),
        "chars": len(text),
        "chars_nospace": len(re.sub(r"\s", "", text)),
        "lines": len(lines),
        "digits": sum(c.isdigit() for c in text),
    }


def load_documents() -> pd.DataFrame:
    """One row per per-sample ground-truth file with its metrics."""
    rows = []
    for fname in sorted(os.listdir(PER_SAMPLE_DIR)):
        m = NAME_RE.match(fname)
        if not m:
            continue
        with open(os.path.join(PER_SAMPLE_DIR, fname), encoding="utf-8") as fh:
            text = fh.read()
        row = {
            "file": fname,
            "template": int(m.group(1)),
            "sample": int(m.group(2)),
            **document_metrics(text),
        }
        rows.append(row)
    df = pd.DataFrame(rows).sort_values(["template", "sample"]).reset_index(drop=True)
    if df.empty:
        raise SystemExit(f"No ground-truth files found under {PER_SAMPLE_DIR}")
    return df


def fmt_mean_sd(series: pd.Series) -> str:
    return f"{series.mean():.1f} ({series.std(ddof=1):.1f})"


def fmt_median_iqr(series: pd.Series) -> str:
    # Linear interpolation (NumPy default) is the conventional Q1/Q3.
    q1, med, q3 = np.percentile(series, [25, 50, 75])
    return f"{med:.0f} [{q1:.0f}, {q3:.0f}]"


def summarize_group(g: pd.DataFrame) -> dict:
    out = {"N": len(g)}
    for metric, label in METRICS.items():
        out[f"{label} — Mean (SD)"] = fmt_mean_sd(g[metric])
        out[f"{label} — Median [Q1, Q3]"] = fmt_median_iqr(g[metric])
    return out


def build_table(df: pd.DataFrame, types: dict | None) -> pd.DataFrame:
    rows = []
    for template, g in df.groupby("template"):
        row = {"Template": str(template)}
        if types is not None:
            row["Document type"] = types.get(template, "")
        row.update(summarize_group(g))
        rows.append(row)

    overall = {"Template": "Overall"}
    if types is not None:
        overall["Document type"] = ""
    overall.update(summarize_group(df))
    rows.append(overall)

    return pd.DataFrame(rows)


def load_types(path: str) -> dict:
    t = pd.read_csv(path)
    if not {"template", "doc_type"}.issubset(t.columns):
        raise SystemExit("--types CSV must have columns: template,doc_type")
    return dict(zip(t["template"].astype(int), t["doc_type"].astype(str)))


def to_markdown(table: pd.DataFrame) -> str:
    header = "| " + " | ".join(table.columns) + " |"
    sep = "| " + " | ".join("---" for _ in table.columns) + " |"
    body = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in table.itertuples(index=False)
    ]
    return "\n".join([header, sep, *body])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--types",
        help="CSV with columns template,doc_type to add a document-type column.",
    )
    ap.add_argument(
        "--out",
        default=os.path.join(BASE, "docs"),
        help="Directory for the CSV outputs (default: docs/).",
    )
    args = ap.parse_args()

    types = load_types(args.types) if args.types else None

    df = load_documents()
    table = build_table(df, types)

    os.makedirs(args.out, exist_ok=True)
    per_doc_path = os.path.join(args.out, "summary_per_document.csv")
    table_path = os.path.join(args.out, "table1_per_template.csv")
    df.to_csv(per_doc_path, index=False)
    table.to_csv(table_path, index=False)

    n_templates = df["template"].nunique()
    print(f"{len(df)} documents across {n_templates} templates.\n")
    print(to_markdown(table))
    print(f"\nWrote {table_path}")
    print(f"Wrote {per_doc_path}")


if __name__ == "__main__":
    main()
