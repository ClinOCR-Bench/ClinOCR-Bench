"""Package the benchmark into a versioned zip for a GitHub Release.

Bundles the end-user benchmark only — the scans, the ground-truth
transcriptions, the one-shot lookups, plus LICENSE and README for orientation.
Source/build artifacts (samples/, templates/, embedded_images/) are excluded.

    python scripts/build_release.py --version v1.0

Writes dist/ClinOCR-Bench-<version>.zip with everything under a top-level
ClinOCR-Bench/ folder, then prints the SHA-256 so it can be recorded in the
release notes.
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (repo-relative path, required?) — directories are added recursively.
CONTENTS: list[tuple[str, bool]] = [
    ("scans", True),
    ("ground_truth", True),
    ("oneshot_lookup.csv", True),
    ("oneshot_lookup.json", True),
    ("LICENSE", True),
    ("README.md", True),
]

ARCHIVE_ROOT = "ClinOCR-Bench"


def _iter_files(src: Path):
    if src.is_dir():
        yield from (p for p in sorted(src.rglob("*")) if p.is_file())
    else:
        yield src


def build(version: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"ClinOCR-Bench-{version}.zip"

    n_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, required in CONTENTS:
            src = ROOT / rel
            if not src.exists():
                if required:
                    raise FileNotFoundError(f"missing required path: {rel}")
                continue
            for f in _iter_files(src):
                arcname = Path(ARCHIVE_ROOT) / f.relative_to(ROOT)
                zf.write(f, arcname)
                n_files += 1

    print(f"wrote {zip_path}  ({n_files} files, "
          f"{zip_path.stat().st_size / 1e6:.1f} MB)")
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"sha256: {sha}")
    return zip_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="release tag, e.g. v1.0")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "dist")
    args = ap.parse_args()
    build(args.version, args.out_dir)


if __name__ == "__main__":
    main()
