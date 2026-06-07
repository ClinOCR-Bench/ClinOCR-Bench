"""One-shot exemplar assignment for ClinOCR-Bench.

Each document is identified by (subset, template, sample). For every subset the
*exemplar* of a template is its lowest available sample; that exemplar is held
out and the remaining samples are the eval documents. Each eval document is
paired with:

  - homogeneous one-shot:  the exemplar of the *same* template.
  - heterogeneous one-shot: the exemplar of a *different* template in the same
    subset, chosen by a cyclic shift that grows with the eval sample's rank:

        donor = base + ((template - base) + rank) % n

    Because 1 <= rank <= #eval < n, the shift is never 0 mod n, so the donor is
    never the query template itself (no self-collision).

For the 1-8 / 9-16 subsets (8 templates, samples 1-8) the exemplar is always
sample 1 and the heterogeneous donor visits all 7 other templates (full
round-robin). The mixed subset keeps 4 sparse, non-contiguous samples per
template, so the exemplar is the min available sample and the donor visits 3
neighbours.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS_DIR = ROOT / "scans"

# base template number, number of templates
SUBSET_RANGE: dict[str, tuple[int, int]] = {
    "normal": (1, 8),
    "handwriting": (1, 8),
    "poor": (1, 8),
    "rotated": (1, 8),
    "tables": (9, 8),
    "mixed": (1, 16),
}

_FNAME = re.compile(r"template_(\d+)_sample_(\d+)_(\w+)\.jpg")


def build_index(scans_dir: Path = SCANS_DIR) -> dict[str, dict[int, list[int]]]:
    """subset -> template -> sorted list of available sample numbers."""
    index: dict[str, dict[int, list[int]]] = {s: {} for s in SUBSET_RANGE}
    for subset in SUBSET_RANGE:
        for f in (scans_dir / subset).iterdir():
            m = _FNAME.match(f.name)
            if not m:
                continue
            template, sample = int(m.group(1)), int(m.group(2))
            index[subset].setdefault(template, []).append(sample)
    for subset in index:
        for template in index[subset]:
            index[subset][template].sort()
    return index


def exemplar_sample(template: int, subset: str,
                    index: dict[str, dict[int, list[int]]]) -> int:
    """The held-out exemplar of a template = its lowest available sample."""
    return index[subset][template][0]


def get_oneshot(template: int, sample: int, subset: str,
                index: dict[str, dict[int, list[int]]]) -> tuple[int, int]:
    """Heterogeneous one-shot exemplar (donor_template, donor_sample)."""
    eval_samples = index[subset][template][1:]  # drop exemplar (min)
    if sample not in eval_samples:
        raise ValueError(
            f"{subset} t{template} s{sample} is an exemplar, not an eval doc")
    rank = eval_samples.index(sample) + 1  # 1-based rank
    base, n = SUBSET_RANGE[subset]
    donor_t = base + ((template - base) + rank) % n
    donor_s = exemplar_sample(donor_t, subset, index)
    return donor_t, donor_s


def build_table(index: dict[str, dict[int, list[int]]]) -> list[dict]:
    """One row per document (all 384), with role and one-shot assignments."""
    rows: list[dict] = []
    for subset in SUBSET_RANGE:
        for template in sorted(index[subset]):
            ex = exemplar_sample(template, subset, index)
            for sample in index[subset][template]:
                row = {
                    "subset": subset,
                    "template": template,
                    "sample": sample,
                }
                if sample == ex:
                    row.update(role="exemplar",
                               homo_template="", homo_sample="",
                               hetero_template="", hetero_sample="")
                else:
                    ht, hs = get_oneshot(template, sample, subset, index)
                    row.update(role="eval",
                               homo_template=template, homo_sample=ex,
                               hetero_template=ht, hetero_sample=hs)
                rows.append(row)
    return rows


def _doc(subset: str, template: int, sample: int) -> dict:
    """Identity + repo-relative paths for one document."""
    stem = f"template_{template}_sample_{sample}_{subset}"
    return {
        "doc_id": f"{subset}_t{template}_s{sample}",
        "subset": subset,
        "template": template,
        "sample": sample,
        "image": f"scans/{subset}/{stem}.jpg",
        "ground_truth": f"ground_truth/{subset}/{stem}.txt",
    }


def build_lookup(rows: list[dict]) -> list[dict]:
    """Machine-friendly lookup: one entry per eval doc with its one-shots.

    Each entry carries the eval doc's identity + paths and the resolved
    homogeneous / heterogeneous one-shot exemplars (also identity + paths).
    Exemplars are not emitted as entries; they appear only as referenced
    one-shots.
    """
    lookup: list[dict] = []
    for r in rows:
        if r["role"] != "eval":
            continue
        entry = _doc(r["subset"], r["template"], r["sample"])
        entry["homo_oneshot"] = _doc(
            r["subset"], r["homo_template"], r["homo_sample"])
        entry["hetero_oneshot"] = _doc(
            r["subset"], r["hetero_template"], r["hetero_sample"])
        lookup.append(entry)
    return lookup


if __name__ == "__main__":
    index = build_index()
    rows = build_table(index)
    out = ROOT / "oneshot_lookup.csv"
    fields = ["subset", "template", "sample", "role",
              "homo_template", "homo_sample", "hetero_template", "hetero_sample"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    lookup = build_lookup(rows)
    out_json = ROOT / "oneshot_lookup.json"
    with out_json.open("w") as f:
        json.dump(lookup, f, indent=2)

    n_eval = sum(r["role"] == "eval" for r in rows)
    n_ex = sum(r["role"] == "exemplar" for r in rows)
    print(f"wrote {len(rows)} rows -> {out}  ({n_eval} eval, {n_ex} exemplar)")
    print(f"wrote {len(lookup)} eval entries -> {out_json}")

    # sanity checks
    for r in rows:
        if r["role"] != "eval":
            continue
        assert r["hetero_template"] != r["template"], f"self-collision: {r}"
        donor = (r["subset"], r["hetero_template"], r["hetero_sample"])
        assert r["hetero_sample"] in index[r["subset"]][r["hetero_template"]], \
            f"donor missing: {donor}"
    print("checks passed: no self-collisions, all donor files exist")
