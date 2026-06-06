"""Create one ground-truth .txt per scan image.

Each scan in scans/<category>/template_X_sample_Y_<category>.jpg shares its
textual content with all other renderings of the same template+sample. The
audited per-sample text lives in ground_truth_per_sample/template_X_sample_Y.txt.

This script walks every scan, derives its template+sample base, and writes the
corresponding per-sample text to ground_truth/<category>/<scan_stem>.txt so the
output mirrors the scans/ directory layout (one subfolder per category, filename
matching the scan exactly).

Final output: 384 text files (one per scan).

NOTE: This does not touch ground_truth_per_sample/ (the manually audited
source). It only reads from it.
"""

import os
import re
import shutil

BASE = os.path.join(os.path.dirname(__file__), "..")
SCANS_DIR = os.path.join(BASE, "scans")
PER_SAMPLE_DIR = os.path.join(BASE, "ground_truth_per_sample")
OUTPUT_DIR = os.path.join(BASE, "ground_truth")

# Matches "template_<int>_sample_<int>" at the start of a scan filename.
BASE_RE = re.compile(r"^(template_\d+_sample_\d+)_[a-z]+\.jpg$")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0
    for category in sorted(os.listdir(SCANS_DIR)):
        cat_dir = os.path.join(SCANS_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        out_cat_dir = os.path.join(OUTPUT_DIR, category)
        os.makedirs(out_cat_dir, exist_ok=True)

        for fname in sorted(os.listdir(cat_dir)):
            if not fname.endswith(".jpg"):
                continue
            m = BASE_RE.match(fname)
            if not m:
                raise ValueError(f"Unexpected scan filename: {fname}")
            sample_base = m.group(1)  # e.g. template_1_sample_2

            src_txt = os.path.join(PER_SAMPLE_DIR, f"{sample_base}.txt")
            if not os.path.exists(src_txt):
                raise FileNotFoundError(
                    f"No per-sample ground truth for {fname}: missing {src_txt}"
                )

            out_txt = os.path.join(out_cat_dir, fname.replace(".jpg", ".txt"))
            shutil.copyfile(src_txt, out_txt)
            count += 1

    print(f"Done. Wrote {count} text files to {OUTPUT_DIR}")
    if count != 384:
        raise SystemExit(f"Expected 384 files, wrote {count}")


if __name__ == "__main__":
    main()
