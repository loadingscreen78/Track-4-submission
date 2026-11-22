# Team SpectraCore — Track 4 submission checklist

Prepared 22 Nov 2026 from the code zip (`Camspector-2.0-results-main`), the student kit
(`TEAM_README.md`, `manifest.csv`, `supported_classes.json`) and the organisers' email
"Updated Track 04" (20 Nov 2026).

## Done

| Item | Where |
|---|---|
| Upload folder named after `TEAM_ID` | `SpectraCore/` |
| `run.sh <video.mp4> <out.json>` | `SpectraCore/run.sh` |
| Output format fixed to the kit (6 fields, `team_id` "SpectraCore") | `code/camspector/contract.py` |
| Model path, training-free: CLIP label, interaction- and diversity-aware highlights, actions | `code/camspector/zeroshot.py`, `clip_encoder.py` |
| `validate.py` (organisers asked teams to write their own) | `SpectraCore/validate.py` |
| One-video-at-a-time runner (no big disk needed, resumable) | `code/scripts/stream_run.py` |
| Free cloud GPU notebook (Google Colab) | `SpectraCore/notebooks/SpectraCore_Colab_run.ipynb` |
| README (setup, architecture, reproduction) | `SpectraCore/README.md` |
| Presentation on the official template | `SpectraCore/presentation/CAMSPECTOR_SpectraCore_Track4.pptx` |
| Tests: format, validator, model heads (54 pass) | `code/tests/` |

## What you still do (no GPU and no free space needed on your laptop)

1. Upload `SpectraCore_Track4_Submission.zip` to **My Drive** (top level).
2. Open `SpectraCore/notebooks/SpectraCore_Colab_run.ipynb` in Google Colab
   (colab.research.google.com → Upload), set **Runtime → Change runtime type → T4 GPU**,
   then **Runtime → Run all**.
   - It downloads CLIP once, gets the FPVSum videos, then downloads, processes and deletes the
     EPIC videos one at a time. Results go to Drive, so a disconnect just means "Run all" again.
   - If YouTube blocks Colab, download the 47 FPVSum videos on another device with the
     official crawler and put them in **My Drive/SpectraCore_fpvsum_videos** as `<video_id>.mp4`.
3. When it finishes, check the last cell says **RESULT: PASS** (185 of 185 scored videos covered).
   **My Drive/SpectraCore_upload.zip** is then the complete `SpectraCore/` folder with
   `outputs/` (185 JSONs) and `weights/` (CLIP + verb prior), ready to submit.
4. Push the code to GitHub (without `weights/`, `data/` and videos; `.gitignore` already does this)
   and confirm the link in the deck and README: `https://github.com/loadingscreen78/Camspector-2.0-results`.
5. Check the spelling "Jagannath Samrtha Mishra" (cover slide, README).
6. Slide 7 has `Demo video: [link]`. No demo-video rule was found in the kit or email: add a link or delete it.
7. The email attached an updated `TEAM_README.md.docx` and `skiing_03.json.docx` that were not
   shared with Claude. Compare them with the README used here in case the format changed.

## Honest expectations

- The model path is training-free (CLIP zero-shot). It was tested on synthetic data, not on the
  real videos: the first real run is the notebook above. It is not scored yet, and FPVSum and
  EPIC validation labels are hidden test labels, so we cannot score it ourselves.
- Expected strengths: video label (distinct sports are easy for CLIP), and highlights spread over
  visually different moments (what coverage rewards). Expected weakness: action mAP, since zero-shot
  verb–noun timing is rough; it is still better than the previous 0.
- If anything in the model path fails for a video, that video gets the baseline instead, so every
  file stays valid.
