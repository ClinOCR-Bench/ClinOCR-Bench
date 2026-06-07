---
license: mit
pretty_name: ClinOCR-Bench
language:
- en
task_categories:
- image-to-text
tags:
- ocr
- clinical
- healthcare
- documents
- benchmark
size_categories:
- n<1K
configs:
- config_name: normal
  data_files:
  - split: train
    path: normal/train-*
  - split: test
    path: normal/test-*
- config_name: handwriting
  data_files:
  - split: train
    path: handwriting/train-*
  - split: test
    path: handwriting/test-*
- config_name: poor
  data_files:
  - split: train
    path: poor/train-*
  - split: test
    path: poor/test-*
- config_name: rotated
  data_files:
  - split: train
    path: rotated/train-*
  - split: test
    path: rotated/test-*
- config_name: tables
  data_files:
  - split: train
    path: tables/train-*
  - split: test
    path: tables/test-*
- config_name: mixed
  data_files:
  - split: train
    path: mixed/train-*
  - split: test
    path: mixed/test-*
---

# ClinOCR-Bench

A benchmark for evaluating Optical Character Recognition (OCR) systems on clinical documents.

> 📦 This dataset loads directly with `datasets` (see [Usage](#usage)). The source code,
> construction scripts, and figures live in the GitHub repository: [ClinOCR-Bench](https://github.com/ClinOCR-Bench/ClinOCR-Bench),
> where the benchmark is also published as a downloadable zip of raw files on each
> release. This card and the repo
> point to each other.

## Overview

Scanned documents have been a headache in healthcare for decades. In the real world they arrive as faxed
referrals, crumpled printouts, photographed forms, handwritten notes, and dense tabular reports —
often combining several of these challenges at once. **ClinOCR-Bench** captures this richness of artifacts in a
single, systematically organized benchmark so that OCR systems can be evaluated across the full
range of conditions.

The dataset is split into subsets, each isolating a distinct document artifact (handwriting,
poor-quality scans, rotation, and tables), plus a *mixed* subset that combines multiple artifacts
to reflect the most challenging real-world cases. Every document is paired with a clean,
human-audited ground-truth transcription.

## File Structure

The dataset spans **6 subsets**, **16 templates**, and **384 documents** (64 per subset). Template 1 to 8 are used by the `Normal-quality`, `Handwriting`, `Poor-quality`, and `Rotation` subsets, while template 9 to 16 are used by the `Tables` subset. The `Mixed artifacts` subset includes 4 samples of templates 1 to 16 (N=64).

Document images, grouped by artifact subset:

| Subset | Config | Description |
| --- | --- | --- |
| Normal-quality | `normal` | Clean, well-scanned documents |
| Handwriting | `handwriting` | Documents rendered with handwriting fonts |
| Poor-quality | `poor` | Low-resolution, photographed, crumbled, or degraded scans |
| Rotation | `rotated` | Rotated / skewed documents |
| Tables | `tables` | Documents dominated by complex tabular layouts |
| Mixed artifacts | `mixed` | Documents combining multiple artifacts (e.g., rotation + highlight + low-resolution) |

Each row carries the following columns:

| Column | Type | Description |
| --- | --- | --- |
| `doc_id` | string | Unique document key, e.g. `handwriting_t3_s5` |
| `image` | image | The scanned document |
| `ground_truth` | string | Human-audited transcription |
| `subset` | string | Artifact subset |
| `template` | int | Template (layout) id |
| `sample` | int | Sample id within the template |
| `homo_id` | string | *(test only)* `doc_id` of the homogeneous one-shot exemplar |
| `hetero_id` | string | *(test only)* `doc_id` of the heterogeneous one-shot exemplar |

## Methodology

The dataset was constructed through a multi-stage pipeline that builds realistic synthetic clinical
documents and then degrades them to mimic real-world scanning artifacts:

1. **Template design** — Manually create a template layout based on real-world scanned documents.
2. **Visual asset generation** — Prompt image-generation models to create logos, barcodes, and
   medical images to be embedded in the documents.
3. **Content generation** — Prompt LLMs to create realistic content for each text area (patient information, impression, notes, etc).
4. **Styling** — Adopt handwriting fonts and adjust table layouts.
5. **Physical artifact simulation** — Print out, crumple, apply plastic folders, multi-generation
   copy, reduce resolution, and rotate to introduce real-world scan artifacts.
6. **Quality control** — Audit and revise through group discussion.

Ground-truth text is extracted programmatically from the source Word documents and then audited.
See the GitHub repository for the full construction pipeline and figures.

## Train / Test split and one-shot setup

ClinOCR-Bench is designed for both zero-shot and one-shot evaluation. Within every
subset, each template contributes a small **exemplar** pool (the *train* split) that is
held out from scoring, and the remaining documents are the **eval** set (the *test*
split):

- **Exemplar (train).** For each template, the lowest-numbered sample is held out as
  that template's exemplar. This gives **56 exemplars** (one per template per subset:
  8 each for `normal`/`handwriting`/`poor`/`rotated`/`tables`, 16 for `mixed`).
- **Eval (test).** Every other document is scored — **328 documents** in total.

Each eval document comes with two predefined one-shot demonstrations, so results are
directly comparable across systems:

- **Homogeneous one-shot** — the exemplar of the *same* template (same layout as the
  query). This mimics a real-world scenario where many scanned documents are based on the same medical form. 

- **Heterogeneous one-shot** — the exemplar of a *different* template in the *same*
  subset, picked by a cyclic shift that grows with the query's rank so it never
  collides with the query template. This reflects another scenario where scanned documents are imported from different sources, with diverse layouts.

This supports three standard regimes: **0-shot**, **1-shot (homogeneous)**, and
**1-shot (heterogeneous)**.

## Usage

```python
from datasets import load_dataset

# pick a subset: normal | handwriting | poor | rotated | tables | mixed
ds = load_dataset("<org>/ClinOCR-Bench", "handwriting")
test, exemplars = ds["test"], ds["train"]

# one-shot demos are referenced by id; resolve against the train split
by_id = {row["doc_id"]: row for row in exemplars}
item = test[0]
homo_demo = by_id[item["homo_id"]]      # same-template exemplar
hetero_demo = by_id[item["hetero_id"]]  # sibling-template exemplar

# item["image"], item["ground_truth"] are the query; *_demo carry the shots
```

## License

Released under the [MIT License](https://opensource.org/license/mit).

## Citation

<!-- TODO: add citation / BibTeX. -->
