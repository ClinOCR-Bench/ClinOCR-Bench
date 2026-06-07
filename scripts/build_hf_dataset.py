"""Build the ClinOCR-Bench Hugging Face dataset from oneshot_lookup.json.

Layout (settled in HF_DISTRIBUTION_NOTES.md + the one-shot design):

  - One **config per subset**: normal, handwriting, poor, rotated, tables, mixed.
    Load with `load_dataset("<repo>", "<subset>")`.
  - Two **splits** per config:
      train = exemplars  (the held-out few-shot pool, 1 per template)
      test  = eval docs  (everything scored)
  - One-shot demos are referenced, not duplicated: each `test` row carries
    `homo_id` / `hetero_id` pointing at `doc_id`s in the same config's `train`
    split. Resolve them with a one-line lookup to fetch the demo image + text.

Row schema (identical across both splits):
    doc_id        str    unique key, e.g. "handwriting_t3_s5"
    image         Image  the scan
    ground_truth  str    transcription
    subset        str
    template      int
    sample        int
    homo_id       str    test: same-template exemplar's doc_id; train: ""
    hetero_id     str    test: sibling-template exemplar's doc_id; train: ""

The eval/exemplar split and the one-shot pairing are read straight from
oneshot_lookup.json (regenerate it with scripts/oneshot.py).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset, DatasetDict, Features, Image, Value

ROOT = Path(__file__).resolve().parent.parent
LOOKUP = ROOT / "oneshot_lookup.json"

SUBSETS = ["normal", "handwriting", "poor", "rotated", "tables", "mixed"]

FEATURES = Features({
    "doc_id": Value("string"),
    "image": Image(),
    "ground_truth": Value("string"),
    "subset": Value("string"),
    "template": Value("int32"),
    "sample": Value("int32"),
    "homo_id": Value("string"),
    "hetero_id": Value("string"),
})


def _read_gt(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _row(node: dict, homo_id: str = "", hetero_id: str = "") -> dict:
    """A dataset row from a lookup node (eval entry or one-shot sub-dict)."""
    return {
        "doc_id": node["doc_id"],
        "image": str(ROOT / node["image"]),
        "ground_truth": _read_gt(node["ground_truth"]),
        "subset": node["subset"],
        "template": node["template"],
        "sample": node["sample"],
        "homo_id": homo_id,
        "hetero_id": hetero_id,
    }


def build() -> DatasetDict | dict[str, DatasetDict]:
    lookup = json.loads(LOOKUP.read_text())

    # Per subset: test rows (eval) + train rows (exemplars, deduped by doc_id).
    test_rows: dict[str, list[dict]] = {s: [] for s in SUBSETS}
    train_rows: dict[str, dict[str, dict]] = {s: {} for s in SUBSETS}

    for e in lookup:
        s = e["subset"]
        homo, hetero = e["homo_oneshot"], e["hetero_oneshot"]
        test_rows[s].append(_row(e, homo["doc_id"], hetero["doc_id"]))
        # exemplars surface only as referenced one-shots; dedupe them
        for ex in (homo, hetero):
            train_rows[s].setdefault(ex["doc_id"], _row(ex))

    configs: dict[str, DatasetDict] = {}
    for s in SUBSETS:
        train = sorted(train_rows[s].values(), key=lambda r: r["doc_id"])
        test = sorted(test_rows[s], key=lambda r: r["doc_id"])
        configs[s] = DatasetDict({
            "train": Dataset.from_list(train, features=FEATURES),
            "test": Dataset.from_list(test, features=FEATURES),
        })
    return configs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="HF repo id, e.g. you/ClinOCR-Bench")
    ap.add_argument("--push", action="store_true",
                    help="push to the Hub (requires --repo and HF auth)")
    ap.add_argument("--private", action="store_true",
                    help="create/push the repo as private")
    ap.add_argument("--save-dir", type=Path,
                    help="optional: save_to_disk under this dir for inspection")
    args = ap.parse_args()

    configs = build()

    for s in SUBSETS:
        dd = configs[s]
        print(f"{s:12s}  train={len(dd['train']):3d}  test={len(dd['test']):3d}")
    n_train = sum(len(dd["train"]) for dd in configs.values())
    n_test = sum(len(dd["test"]) for dd in configs.values())
    print(f"{'total':12s}  train={n_train:3d}  test={n_test:3d}")

    if args.save_dir:
        for s, dd in configs.items():
            dd.save_to_disk(str(args.save_dir / s))
        print(f"saved to {args.save_dir}")

    if args.push:
        if not args.repo:
            ap.error("--push requires --repo")
        for s, dd in configs.items():
            dd.push_to_hub(args.repo, config_name=s, private=args.private)
            print(f"pushed config '{s}' -> {args.repo}")


if __name__ == "__main__":
    main()
