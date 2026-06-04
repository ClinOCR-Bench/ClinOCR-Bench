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

The dataset spans **6 subsets**, **16 templates**, and **384 documents** (64 per subset). Template 1 to 8 are used by the `Normal-quality`, `Handwriting`, `Poor-quality`, and `Rotation` subsets, while template 9 to 16 are used for by `Tables` subset. The `Mixed artifacts` subset includes 4 samples of templates 1 to 16 (N=64). 

<p align="center">
  <img src="docs/readme_images/file_structure_diagram.png" alt="File structure of ClinOCR-Bench" width="500">
</p>


Document images, grouped by artifact subset:

| Subset | Folder | Description |
| --- | --- | --- |
| Normal-quality | [`scans/normal/`](scans/normal/) | Clean, well-scanned documents |
| Handwriting | [`scans/handwriting/`](scans/handwriting/) | Documents rendered with handwriting fonts |
| Poor-quality | [`scans/poor/`](scans/poor/) | Low-resolution, photographed, crumbled, or degraded scans |
| Rotation | [`scans/rotated/`](scans/rotated/) | Rotated / skewed documents |
| Tables | [`scans/tables/`](scans/tables/) | Documents dominated by complex tabular layouts |
| Mixed artifacts | [`scans/mixed/`](scans/mixed/) | Documents combining multiple artifacts (e.g., rotation + highlight + low-resolution) |

## Methodology

The dataset was constructed through a multi-stage pipeline that builds realistic synthetic clinical
documents and then degrades them to mimic real-world scanning artifacts.

<p align="center">
  <img src="docs/readme_images/method_flowchart.png" alt="Dataset construction methodology" width="800">
</p>

1. **Template design** — Manually create a template layout based on real-world scanned documents.
2. **Visual asset generation** — Prompt image-generation models to create logos, barcodes, and
   medical images to be embedded in the documents.
3. **Content generation** — Prompt LLMs to create realistic content for each text area (patient information, impression, notes, etc).
4. **Styling** — Adopt handwriting fonts and adjust table layouts.
5. **Physical artifact simulation** — Print out, crumple, apply plastic folders, multi-generation
   copy, reduce resolution, and rotate to introduce real-world scan artifacts.
6. **Quality control** — Audit and revise through group discussion.

Ground-truth text is extracted programmatically from the source Word documents
(see [`scripts/preprocess_ground_truth.py`](scripts/preprocess_ground_truth.py)) and then audited.

## Data Accessibility

The full dataset is available on the Hugging Face Hub.

<!-- TODO: add the Hugging Face dataset link and loading instructions once the dataset is published. -->

## License

<!-- TODO: specify the license. -->

## Citation

<!-- TODO: add citation / BibTeX. -->
