# ClinOCR-Bench

A benchmark for evaluating Optical Character Recognition (OCR) systems on clinical documents.

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

<p align="center">
  <img src="docs/readme_images/overview_diagram.png" alt="Overview of the ClinOCR-Bench subsets" width="800">
</p>

<!-- TODO: add summary statistics, motivation, and intended use cases. -->

## File Structure

The dataset spans **6 subsets**, **16 templates**, and **384 documents** (64 per subset). Template 1 to 8 are used by the `Normal-quality`, `Handwriting`, `Poor-quality`, and `Rotation` subsets, while template 9 to 16 are used by the `Tables` subset. The `Mixed artifacts` subset includes 4 samples of templates 1 to 16 (N=64). 

<p align="center">
  <img src="docs/readme_images/file_structure_diagram.png" alt="File structure of ClinOCR-Bench" width="500">
</p>


Document images, grouped by artifact subset:

| Subset | Images | Ground truth | Description |
| --- | --- | --- | --- |
| Normal-quality | `scans/normal/` | `ground_truth/normal/` | Clean, well-scanned documents |
| Handwriting | `scans/handwriting/` | `ground_truth/handwriting/` | Documents rendered with handwriting fonts |
| Poor-quality | `scans/poor/` | `ground_truth/poor/` | Low-resolution, photographed, crumbled, or degraded scans |
| Rotation | `scans/rotated/` | `ground_truth/rotated/` | Rotated / skewed documents |
| Tables | `scans/tables/` | `ground_truth/tables/` | Documents dominated by complex tabular layouts |
| Mixed artifacts | `scans/mixed/` | `ground_truth/mixed/` | Documents combining multiple artifacts (e.g., rotation + highlight + low-resolution) |

## Methodology

The dataset was constructed through a multi-stage workflow that builds realistic synthetic clinical
documents and then degrades them to mimic real-world scanning artifacts.

<p align="center">
  <img src="docs/readme_images/method_flowchart.png" alt="Dataset construction methodology" width="800">
</p>

1. **Template design** — Manually create a template layout based on real-world scanned documents.
2. **Embedded image generation** — Prompt image-generation models to create logos, barcodes, and
   medical images to be embedded in the documents.
3. **Content generation** — Prompt LLMs to create realistic content for each text area (patient information, impression, notes, etc).
4. **Styling** — Adopt handwriting fonts and adjust table layouts.
5. **Physical artifact simulation** — Print out, crumple, apply plastic folders, multi-generation
   copy, reduce resolution, and rotate to introduce real-world scan artifacts.
6. **Quality control** — Audit and revise through group discussion.

Ground-truth text is extracted programmatically from the source Word documents followed by manual audit.

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

The full mapping is available:

- [`oneshot_lookup.csv`](oneshot_lookup.csv) — one row per document with its role and donor templates/samples.
- [`oneshot_lookup.json`](oneshot_lookup.json) — one entry per eval document, each pointing to its homogeneous and heterogeneous one-shot exemplars (with image and ground-truth paths).

## Data Accessibility

The benchmark is distributed two ways:

- **Direct download (raw files).** A single zip — `scans/`, `ground_truth/`, and the
  one-shot lookups — is attached to each GitHub Release. No
  account or special tooling required; just download and unzip.
  
- **Hugging Face Hub (`load_dataset`).** The same data as a `datasets`-library dataset,
  with **one config per subset** and a `train` (exemplar) / `test` (eval) split each:

```python
from datasets import load_dataset

# pick a subset: normal | handwriting | poor | rotated | tables | mixed
ds = load_dataset("ClinOCR-Bench/ClinOCR-Bench", "handwriting")
test, exemplars = ds["test"], ds["train"]

# one-shot demos are referenced by id; resolve against the train split
by_id = {row["doc_id"]: row for row in exemplars}
item = test[0]
homo_demo = by_id[item["homo_id"]]      # same-template exemplar
hetero_demo = by_id[item["hetero_id"]]  # sibling-template exemplar

# item["image"], item["ground_truth"] are the query; *_demo carry the shots
```

## License

Released under the [MIT License](LICENSE).

## Citation

<!-- TODO: add citation / BibTeX. -->
