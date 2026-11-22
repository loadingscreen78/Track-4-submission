#!/usr/bin/env python3
"""Run the whole Track 4 manifest with almost no disk: one EPIC video at a time.

For every manifest video (the 2 Scuba videos excluded by the organisers are skipped):
  EPIC-KITCHENS-100 -> download that one video (official downloader) -> run -> delete it
  FPVSum            -> read it from --fpvsum-dir (the 47 videos are small; download them first)

Peak disk = the largest single EPIC video (a few GB) + CLIP weights (~600 MB).
Resumable: a video whose JSON already exists and validates is skipped, so a disconnected
Colab/Kaggle session simply continues where it stopped. CPU works; a GPU is ~10x faster.

Usage:
  python code/scripts/stream_run.py --out outputs/ --fpvsum-dir /path/to/fpvsum_videos
Options:
  --work DIR        temporary download folder (default: .cache/epic_tmp)
  --epic-dir DIR    use EPIC videos already on disk instead of downloading
  --only epic|fpvsum
  --keep            do not delete downloaded EPIC videos
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from camspector import contract as C  # noqa: E402
from camspector.pipeline import process  # noqa: E402

DL_REPO = "https://github.com/epic-kitchens/epic-kitchens-download-scripts"
DL_DIR = ROOT / ".cache" / "epic-kitchens-download-scripts"
VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi"}
DATASET = {"epic": "epic_kitchens_100", "fpvsum": "fpvsum"}

log = logging.getLogger("stream_run")


def load_validator():
    spec = importlib.util.spec_from_file_location("validate", ROOT / "validate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_video(root: Path | None, vid: str) -> Path | None:
    if root is None or not Path(root).exists():
        return None
    for p in Path(root).rglob("*"):
        if p.is_file() and p.suffix.lower() in VIDEO_EXT and p.stem == vid:
            return p
    return None


def download_epic(vid: str, work: Path) -> Path | None:
    if not (DL_DIR / "epic_downloader.py").exists():
        DL_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", DL_REPO, str(DL_DIR)], check=True)
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "epic_downloader.py", "--videos", "--specific-videos", vid,
                    "--output-path", str(work)], cwd=DL_DIR, check=True)
    return find_video(work, vid)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "outputs")
    ap.add_argument("--fpvsum-dir", type=Path, default=None)
    ap.add_argument("--epic-dir", type=Path, default=None)
    ap.add_argument("--work", type=Path, default=ROOT / ".cache" / "epic_tmp")
    ap.add_argument("--only", choices=sorted(DATASET), default=None)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--log", type=Path, default=ROOT / "experiments" / "run_log.csv")
    a = ap.parse_args(argv)
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    V = load_validator()
    with open(C.MANIFEST_PATH, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["video_id"] not in C.EXCLUDED_VIDEO_IDS]
    if a.only:
        rows = [r for r in rows if r["dataset"] == DATASET[a.only]]
    mref = V.load_manifest(C.MANIFEST_PATH)
    classes = V.load_classes(C.SUPPORTED_CLASSES_PATH)
    a.out.mkdir(parents=True, exist_ok=True)
    a.log.parent.mkdir(parents=True, exist_ok=True)
    new_log = not a.log.exists()
    logf = open(a.log, "a", newline="", encoding="utf-8")
    w = csv.writer(logf)
    if new_log:
        w.writerow(["video_id", "dataset", "status", "model_used", "seconds"])

    counts = {"done_before": 0, "ok": 0, "fallback": 0, "failed": 0}
    for i, r in enumerate(rows, 1):
        vid, ds = r["video_id"], r["dataset"]
        out = a.out / f"{vid}.json"
        if out.exists() and not V.validate_file(out, mref, classes)[1]:
            counts["done_before"] += 1
            continue
        log.info("[%d/%d] %s (%s, %.0f s)", i, len(rows), vid, ds, float(r["duration_sec"]))
        t0, path, downloaded, used_model, status = time.time(), None, False, None, ""
        try:
            if ds == DATASET["epic"]:
                path = find_video(a.epic_dir, vid)
                if path is None:
                    path, downloaded = download_epic(vid, a.work), True
            else:
                path = find_video(a.fpvsum_dir, vid)
            if path is None:
                raise FileNotFoundError(f"video file for {vid} not found")
            info = process(path, out)
            used_model = info.get("used_model")
            errs = V.validate_file(out, mref, classes)[1]
            status = "ok" if not errs else f"invalid: {errs[0]}"
            counts["ok" if not errs else "failed"] += 1
            if used_model is False:
                counts["fallback"] += 1
        except Exception as e:  # keep going: one bad video must not stop the run
            status = f"failed: {e}"
            counts["failed"] += 1
            log.error("%s: %s", vid, e)
        finally:
            if downloaded and path is not None and not a.keep:
                path.unlink(missing_ok=True)
        w.writerow([vid, ds, status, used_model, round(time.time() - t0, 1)])
        logf.flush()
    logf.close()
    log.info("summary: %s", counts)
    if counts["fallback"]:
        log.warning("%d video(s) used the baseline fallback: check the log for 'model path failed'",
                    counts["fallback"])
    return V.main(["--dir", str(a.out)])


if __name__ == "__main__":
    sys.exit(main())
