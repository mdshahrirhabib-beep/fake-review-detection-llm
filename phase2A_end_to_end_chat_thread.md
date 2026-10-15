# End-to-End Chat Thread — Phase 2A Artifact Preservation, Historical Refit, and Next-Step Planning

> **Scope:** This Markdown transcript contains the user-visible chat thread from the point where we began discussing how to preserve the Full RS-1 artifact outside Kaggle through the Historical RS-4H refit, checksum verification, and transition toward held-out inference.
>
> Internal system/developer instructions and private reasoning are not part of the user-visible chat and are therefore not included.

---

## 1. User

How do I ensure the full artifact ZIP has been safely saved outside the temporary Kaggle runtim

## 1. Assistant

Yes. Before we start RS-4H, I want you to **physically copy the Full artifact ZIP from Kaggle to your own computer** and verify that the copy is intact. That is the safest definition of “saved outside the temporary Kaggle runtime.”

First, while the current Kaggle session is still open, run this small cell:

```python
from pathlib import Path
import hashlib

p = Path(
    "/kaggle/working/phase2A_RS1_FULL/"
    "phase2A_RS1_FULL_ARTIFACT.zip"
)

assert p.exists(), "ZIP NOT FOUND"

h = hashlib.sha256()
with open(p, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)

print("File:", p)
print("Size:", f"{p.stat().st_size / (1024**2):.2f} MB")
print("SHA256:", h.hexdigest())

EXPECTED = "12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545"

assert h.hexdigest() == EXPECTED
print("\n✓ ORIGINAL KAGGLE ZIP VERIFIED")
```

You should get:

```text
✓ ORIGINAL KAGGLE ZIP VERIFIED
```

Then download this exact file from Kaggle:

```text
/kaggle/working/phase2A_RS1_FULL/
phase2A_RS1_FULL_ARTIFACT.zip
```

In Kaggle, open the notebook's **Files / Output** panel, navigate to:

```text
kaggle
└── working
    └── phase2A_RS1_FULL
        └── phase2A_RS1_FULL_ARTIFACT.zip
```

Click the ZIP and choose **Download**.

### After it downloads to your Windows computer

Do **not** assume that seeing the file in Downloads is enough. We should verify its SHA-256.

Open **PowerShell** in Windows and run something like:

```powershell
Get-FileHash "C:\Users\YOUR_NAME\Downloads\phase2A_RS1_FULL_ARTIFACT.zip" -Algorithm SHA256
```

Windows should return:

```text
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545
```

That must match **exactly**.

If it matches, we have cryptographic evidence that:

```text
Kaggle artifact
       │
       ↓
downloaded copy on your PC
       │
       ↓
same SHA-256
       │
       ↓
identical file ✓
```

At that point the Full artifact is genuinely safe outside the temporary Kaggle runtime.

For extra protection, I recommend making **two external copies**: keep the verified ZIP on your computer and copy the same ZIP to OneDrive/Google Drive or another storage location. Do not rename or unzip the master copy; keep:

```text
phase2A_RS1_FULL_ARTIFACT.zip
```

unchanged as the archival master.

Our recorded checksum is:

```text
Full artifact ZIP SHA256
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545
```

Once you have downloaded it and the Windows SHA matches, tell me **“SHA matched”**. Then we can safely close/restart this Kaggle runtime and proceed to **RS-4H Historical training**.

---

## 2. User

should i go to the files and download the notebook

## 2. Assistant

No — **not the notebook**. What you must download now is the **artifact ZIP** created by F3.

Go to Kaggle’s Files/Output panel and download:

```text
/kaggle/working/phase2A_RS1_FULL/
phase2A_RS1_FULL_ARTIFACT.zip
```

The notebook file is useful to keep too, but it is **not** the trained model artifact. The ZIP contains the saved Full model, tokenizer, registry, training history, and artifact manifest.

So the priority is:

1. Download `phase2A_RS1_FULL_ARTIFACT.zip`
2. Verify its SHA-256 equals:
   `12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545`
3. Then optionally also download/save the notebook for documentation.

Once the ZIP is safely on your computer, we can move to RS-4H Historical training.

---

## 3. User

[Uploaded screenshot]

where

## 3. Assistant

Yes — you are in the correct place.

On the **right-hand panel**, under **Output**, click the small arrow next to:

```text
/kaggle/working
```

Then open:

```text
phase2A_RS1_FULL
```

Inside that folder you should see:

```text
phase2A_RS1_FULL_ARTIFACT.zip
```

Click the ZIP file, then use the **download icon / three-dot menu → Download**.

Your screenshot already confirms the ZIP exists and is correct:

```text
Size: 711.50 MB
SHA256:
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545

✓ ORIGINAL KAGGLE ZIP VERIFIED
```

So just expand **`/kaggle/working` → `phase2A_RS1_FULL`** and download **`phase2A_RS1_FULL_ARTIFACT.zip`** — not the notebook.

---

## 4. User

got it

## 4. Assistant

Perfect. The checksum file you uploaded records the exact expected Full-artifact hash:

`12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545`

Before closing this Kaggle session, do one final 30-second check on the **ZIP you downloaded to your computer**. In Windows PowerShell run:

```powershell
Get-FileHash "C:\Users\YOUR_NAME\Downloads\phase2A_RS1_FULL_ARTIFACT.zip" -Algorithm SHA256
```

It must return exactly:

```text
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545
```

If it matches, the Full artifact is safely preserved and **we never retrain Full again**.

Then our immediate next step is:

**Fresh Tesla T4 runtime → RS-4H Historical final training**

with the frozen contract:

```text
Historical N          = 5,602
Physical batch        = 2
Gradient accumulation = 16
Effective batch       = 32
Epochs executed       = 3
Updates/epoch         = 176
Executed updates      = 528
Scheduler horizon     = 1,408 steps (8-epoch trajectory)
Warmup                = 140
FP32                   = ON
AMP / GradScaler       = OFF
```

Once your downloaded ZIP hash matches, tell me **“SHA matched”** and I’ll move us directly to the RS-4H Historical notebook.

---

## 5. User

```text
 File "/tmp/ipykernel_58/3595686412.py", line 1
    Get-FileHash "C:\Users\YOUR_NAME\Downloads\phase2A_RS1_FULL_ARTIFACT.zip" -Algorithm SHA256
                 ^
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 2-3: truncated \UXXXXXXXX escape
```

## 5. Assistant

That error happened because you pasted a **PowerShell command into a Python/Kaggle cell**.

Do not run this inside Kaggle:

```powershell
Get-FileHash ...
```

Run it on your **Windows computer** instead.

Open **PowerShell** on Windows, then use:

```powershell
Get-FileHash "$HOME\Downloads\phase2A_RS1_FULL_ARTIFACT.zip" -Algorithm SHA256
```

That avoids needing to know your Windows username.

You should see a SHA256 value. It must equal:

```text
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545
```

If you prefer, you can also right-click inside your Downloads folder → **Open in Terminal**, then run:

```powershell
Get-FileHash ".\phase2A_RS1_FULL_ARTIFACT.zip" -Algorithm SHA256
```

Send me the SHA it returns.

---

## 6. User

```text
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          12962BD779AB9523D24736AF2C68823AC66D41C56334261D7341D31991C8E545       C:\Users\Shahriar Habib\Downl...


PS C:\Users\Shahriar Habib>
fwd-i-search: _
```

## 6. Assistant

Yes — **the Full ZIP hash matches exactly**. PowerShell displays hashes in uppercase, but SHA-256 is case-insensitive for comparison.

So your downloaded Full artifact is now safely verified outside Kaggle:

```text
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545
```

That means **RS-4F is closed. Do not retrain Full again.**

I have prepared the next notebook for **RS-4H Historical training**:

`dissertation_PHASE2A_RS1_HISTORICAL_REFIT_MEMORY_SAFE.ipynb`

Notebook SHA-256:

```text
f197f017663a1e7673f5d93c1421ce3da46a0c3934551a9b6ecaaf1fa5636210
```

I specifically checked that it is locked to:

```text
Historical N          = 5,602
Physical batch        = 2
Gradient accumulation = 16
Effective batch       = 32

Microbatches/epoch    = 2,801
Updates/epoch         = 176

Epochs executed       = 3
Executed updates      = 528

Scheduler horizon     = 8 epochs
Scheduler total steps = 1,408
Warmup steps          = 140
```

The notebook also statically verifies that the Historical training cell uses `train_temporal`, not `train_full`, and that no 3-epoch scheduler can accidentally replace the required 8-epoch trajectory.

### What you do now

Start a **fresh Kaggle Tesla T4 session**, upload/open this Historical notebook, attach the same Yelp training dataset, and run only:

```text
H0
```

Send me the H0 output first. We will verify H0 → H1 → H2 before launching the expensive H3 Historical training.

---

## 7. User

```text
================================================================================================
H0 — RS-4H FRESH RUNTIME
================================================================================================
Python       : 3.12.13
PyTorch      : 2.10.0+cu128
Transformers : 5.0.0
GPU          : Tesla T4
Train file   : /kaggle/input/datasets/mdshahrirhabib/yalp-testtrain/new_data_train.csv
Work root    : /kaggle/working/phase2A_RS1_HISTORICAL
Environment SHA256: cc3c4d0d4a856698b3b43bfc5142de0d84c43c65c2df87865abea794254217ee

✓ H0 PASSED — no held-out file was opened
```

## 7. Assistant

H0 passed exactly as required.

The Historical refit is now running in the correct fresh environment:

```text
Python       : 3.12.13
PyTorch      : 2.10.0+cu128
Transformers : 5.0.0
GPU          : Tesla T4
```

The training source resolved correctly, the isolated Historical work directory is correct, and—most importantly—**no held-out file was opened**.

Your H0 environment SHA-256 is:

```text
cc3c4d0d4a856698b3b43bfc5142de0d84c43c65c2df87865abea794254217ee
```

Now run **H1 only**.

H1 should reproduce:

```text
Raw train         = 9,929
Full origin       = 9,926
Historical origin = 5,602
Rows skipped      = 0
```

with these exact fingerprints:

```text
Full:
6539dc98b3517bd778df0d0b4abba1f4beb3f9120ce70bdaa1be540404543195

Historical:
ed4e3a55e0c52f8949873847ba44ac8bebe8de77efd96daacc4cb4c5e592ea2e
```

Send me the complete H1 output before running H2.

---

## 8. User

```text
================================================================================================
H1 — TRAINING-ORIGIN AUDIT
================================================================================================
Raw train        : 9,929
Full origin      : 9,926 | 6539dc98b3517bd778df0d0b4abba1f4beb3f9120ce70bdaa1be540404543195
Historical origin: 5,602 | ed4e3a55e0c52f8949873847ba44ac8bebe8de77efd96daacc4cb4c5e592ea2e
Rows skipped     : 0
Manifest SHA256  : 129cad0419fdee55658a3b31218620173b11687c20ca2d947e70504fcdd8338c

✓ H1 PASSED — exact Full/Historical origins recovered
✓ No held-out test/regime data were loaded
```

## 8. Assistant

H1 passed exactly as required.

The Historical origin is confirmed as the exact frozen dataset:

```text
Historical N:
5,602

Historical fingerprint:
ed4e3a55e0c52f8949873847ba44ac8bebe8de77efd96daacc4cb4c5e592ea2e
```

And importantly:

```text
Rows skipped = 0
No held-out data loaded
```

Your H1 manifest SHA-256 is:

```text
129cad0419fdee55658a3b31218620173b11687c20ca2d947e70504fcdd8338c
```

Now run **H2 only**.

It should verify:

```text
Historical N             = 5,602
Physical batch           = 2
Gradient accumulation    = 16
Effective batch          = 32
Microbatches/epoch       = 2,801
Updates/epoch            = 176

Epochs executed          = 3
Executed updates         = 528

Scheduler horizon epochs = 8
Scheduler total steps    = 1,408
Warmup steps             = 140
```

The critical lines we need at the end are:

```text
✓ H2 PASSED
✓ Historical stops after epoch 3 under the frozen 8-epoch scheduler
✓ Physical batch > 2 is prohibited in RS-4H
```

Send me the complete **H2 output** before starting H3.

---

## 9. User

```text
================================================================================================
H2 — HISTORICAL REFIT CONTRACT
================================================================================================
Model revision           : 8ccc9b6f36199bec6961081d44eb72fb3f7353f3
Historical N             : 5,602
Physical batch           : 2
Gradient accumulation    : 16
Effective batch          : 32
Microbatches/epoch       : 2801
Updates/epoch            : 176
Epochs executed          : 3
Executed updates         : 528
Scheduler horizon epochs : 8
Scheduler total steps    : 1408
Warmup steps             : 140
Contract SHA256          : 724b92639744ada7397dccd80788cc00d77b97eacc8309a20151a300208ed652

✓ H2 PASSED
✓ Historical stops after epoch 3 under the frozen 8-epoch scheduler
✓ Physical batch > 2 is prohibited in RS-4H
```

## 9. Assistant

Excellent — **H2 passed exactly as required.** The Historical training contract is now frozen and internally consistent.

Your authoritative H2 contract SHA-256 is:

```text
724b92639744ada7397dccd80788cc00d77b97eacc8309a20151a300208ed652
```

Everything important is correct:

```text
Historical N             = 5,602
Physical batch           = 2
Gradient accumulation    = 16
Effective batch          = 32

Microbatches / epoch     = 2,801
Updates / epoch          = 176

Epochs actually trained  = 3
Executed updates         = 528

Scheduler horizon        = 8 epochs
Scheduler total steps    = 1,408
Warmup steps             = 140
```

The crucial governance condition is confirmed:

> **3 actual training epochs under the frozen 8-epoch scheduler trajectory.**

So yes: **run H3 now.**

Do not restart this runtime. H0–H2 have not placed a trained DeBERTa model on the GPU, so this is still the clean T4 runtime that H3 expects.

At the beginning, H3 should show GPU memory, tokenization SHA and then the initial whole-model SHA. That initial SHA **must** be:

```text
c66e8175c2e9f031da9bfd766479b4fceed74caa1c47888bf0cdc0f9d15b01d1
```

Then expect three epochs, each with exactly **176 updates**:

```text
Epoch 1/3 → global 176/528
Epoch 2/3 → global 352/528
Epoch 3/3 → global 528/528
```

Do not worry if the final learning rate is **not zero** after epoch 3. In fact, it **should not be zero**, because the scheduler has a 1,408-step horizon and we deliberately stop after update 528. A zero LR at update 528 would indicate the wrong 3-epoch scheduler and would be a problem.

When H3 finishes successfully, we need these final lines:

```text
✓ RS-4H PASSED
✓ Final artifact directory : ...
✓ Export ZIP               : ...
✓ ZIP SHA256               : ...
✓ Registry SHA256          : ...
✓ Artifact manifest SHA256 : ...
✓ No validation or held-out data were used
```

Then **stop**. Download the Historical ZIP and verify its SHA on Windows exactly as we did for Full.

Go ahead with **H3** now and send me the complete output when it finishes.

---

## 10. User

```text
H3 / RS-4H — HISTORICAL FINAL RECOVERY REFIT
================================================================================================
GPU total memory : 14.56 GiB
GPU free memory  : 10.80 GiB
Tokenization SHA256: 403b7892af7b7dc3d23cd7041c705d4f3264fad77db0b95334c958b633226693
```

Loading weights: 100%

```text
DebertaV2ForSequenceClassification LOAD REPORT from: microsoft/deberta-v3-base
Key                                     | Status     |
----------------------------------------+------------+-
lm_predictions.lm_head.LayerNorm.weight | UNEXPECTED |
mask_predictions.LayerNorm.weight       | UNEXPECTED |
mask_predictions.classifier.bias        | UNEXPECTED |
mask_predictions.classifier.weight      | UNEXPECTED |
lm_predictions.lm_head.LayerNorm.bias   | UNEXPECTED |
mask_predictions.dense.bias             | UNEXPECTED |
lm_predictions.lm_head.dense.bias       | UNEXPECTED |
lm_predictions.lm_head.bias             | UNEXPECTED |
lm_predictions.lm_head.dense.weight     | UNEXPECTED |
mask_predictions.LayerNorm.bias         | UNEXPECTED |
mask_predictions.dense.weight           | UNEXPECTED |
pooler.dense.bias                       | MISSING    |
classifier.weight                       | MISSING    |
classifier.bias                         | MISSING    |
pooler.dense.weight                     | MISSING    |

Notes:
- UNEXPECTED : can be ignored when loading from different task/architecture; not ok if you expect identical arch.
- MISSING    : those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.
```

```text
Initial whole-model SHA256: c66e8175c2e9f031da9bfd766479b4fceed74caa1c47888bf0cdc0f9d15b01d1
Historical scheduler verified: 3 executed epochs under 8-epoch / 1,408-step horizon
  Epoch 1/3 | update 050/176 | global 0050/528 | loss_so_far=0.6935
  Epoch 1/3 | update 100/176 | global 0100/528 | loss_so_far=0.6966
  Epoch 1/3 | update 150/176 | global 0150/528 | loss_so_far=0.6968
  Epoch 1/3 | update 176/176 | global 0176/528 | loss_so_far=0.6969

Epoch 1/3 COMPLETE | loss=0.6969 | LR=0.00001943 | 13.15 min | peak_reserved=5.22 GiB
Row-order SHA256: 57c24b97b379f03ee3bd705f9b2c85f752ff71e1dc568133765843b889dbc04e
✓ Atomic resume checkpoint saved after epoch 1
  Epoch 2/3 | update 050/176 | global 0226/528 | loss_so_far=0.6978
  Epoch 2/3 | update 100/176 | global 0276/528 | loss_so_far=0.6891
  Epoch 2/3 | update 150/176 | global 0326/528 | loss_so_far=0.6893
  Epoch 2/3 | update 176/176 | global 0352/528 | loss_so_far=0.6889

Epoch 2/3 COMPLETE | loss=0.6889 | LR=0.00001666 | 13.16 min | peak_reserved=5.22 GiB
Row-order SHA256: 0ef2494e2ee8cc75c0cf70b75cb9a612466ca6547499aeeda9dac68fc47f9504
✓ Atomic resume checkpoint saved after epoch 2
  Epoch 3/3 | update 050/176 | global 0402/528 | loss_so_far=0.6785
  Epoch 3/3 | update 100/176 | global 0452/528 | loss_so_far=0.6705
  Epoch 3/3 | update 150/176 | global 0502/528 | loss_so_far=0.6707
  Epoch 3/3 | update 176/176 | global 0528/528 | loss_so_far=0.6683

Epoch 3/3 COMPLETE | loss=0.6683 | LR=0.00001388 | 13.15 min | peak_reserved=5.22 GiB
Row-order SHA256: 8987d900f310080ca7464c2368de000e7f3cc58c01525cb77bc8062880b4bdb9
✓ Atomic resume checkpoint saved after epoch 3

================================================================================================
HISTORICAL REFIT COMPLETE — FINALISING ARTIFACT
================================================================================================
Final model parameter SHA256: ef4f18684c2f6bb7ad73ceed45ef48f8d7bb7f8ca0d0631c2324a37887233898
```

Writing model shards: 100%

```text
✓ RS-4H PASSED
✓ Final artifact directory : /kaggle/working/phase2A_RS1_HISTORICAL/phase2A_RS1_HISTORICAL_ARTIFACT
✓ Export ZIP               : /kaggle/working/phase2A_RS1_HISTORICAL/phase2A_RS1_HISTORICAL_ARTIFACT.zip
✓ ZIP SHA256               : c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
✓ Registry SHA256          : 63d93758880e8e53318a33de2c882fc492f994ec329c8bc9d96ff4ac299868fb
✓ Artifact manifest SHA256 : 692a2dc35b46a0c2797ed0667ab9c556f4ebf3e020b403ed3724dcfee087020a
✓ Resume checkpoint removed only after successful finalisation
✓ No validation or held-out data were used

STOP. Persist/export the ZIP before moving to held-out inference.
```

## 10. Assistant

RS-4H has **fully passed**. The Historical recovery model is now complete, and the run behaved exactly as designed.

The most important checks all succeeded:

```text
Initial model SHA256
c66e8175c2e9f031da9bfd766479b4fceed74caa1c47888bf0cdc0f9d15b01d1
```

So Historical started from the exact deterministic state validated in RS-3S.

The scheduler is also correct:

```text
Executed epochs      = 3
Executed updates     = 528
Scheduler horizon    = 1,408
Final LR             = 0.00001388
```

That non-zero final LR is **exactly what we wanted**. It confirms this was genuinely 3 epochs executed under the frozen **8-epoch scheduler**, rather than accidentally using a 3-epoch schedule.

Memory was stable throughout:

```text
Peak GPU reserved = 5.22 GiB
```

So the permanent `2 × 16 = effective batch 32` solution has now survived both the Full and Historical real refits. There is no reason to revisit the OOM configuration.

Please preserve these Historical identifiers:

```text
Final model parameter SHA256
ef4f18684c2f6bb7ad73ceed45ef48f8d7bb7f8ca0d0631c2324a37887233898

Historical ZIP SHA256
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b

Registry SHA256
63d93758880e8e53318a33de2c882fc492f994ec329c8bc9d96ff4ac299868fb

Artifact manifest SHA256
692a2dc35b46a0c2797ed0667ab9c556f4ebf3e020b403ed3724dcfee087020a
```

### Do this next — before anything else

Download:

```text
/kaggle/working/phase2A_RS1_HISTORICAL/
phase2A_RS1_HISTORICAL_ARTIFACT.zip
```

Then on Windows PowerShell run:

```powershell
Get-FileHash "$HOME\Downloads\phase2A_RS1_HISTORICAL_ARTIFACT.zip" -Algorithm SHA256
```

It must return:

```text
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

Uppercase/lowercase does not matter.

Once that matches, **both trained RS-1 artifacts are permanently secured**:

```text
FULL
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545

HISTORICAL
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

Then we move to the next major stage: **one-time held-out inference on Regimes A–D** using these frozen models. That stage will load the saved artifacts only—**no retraining**—and immediately persist row-level `reviewID`, `reviewerID`, true label, predicted label and logits so we never lose the predictions again.

Download and verify the Historical ZIP first. Once the SHA matches, send me the result and we move directly to the held-out inference notebook.

---

## 11. User

[Uploaded screenshot]

## 11. Assistant

Yes — you are in the correct **Output** panel.

In your screenshot, `/kaggle/working` is expanded, but you are currently only seeing:

```text
phase2A_RS1
phase2A_RS1_FULL
```

The **Historical folder should be further down** in the same `/kaggle/working` list.

Scroll down in the **right-hand Output panel** until you see:

```text
phase2A_RS1_HISTORICAL
```

Expand it, then you should see:

```text
phase2A_RS1_HISTORICAL_ARTIFACT
phase2A_RS1_HISTORICAL_ARTIFACT.zip
phase2A_RS1_HISTORICAL_ARTIFACT.zip.sha256.txt
...
```

Download this exact file:

```text
phase2A_RS1_HISTORICAL_ARTIFACT.zip
```

The expected ZIP is about the same scale as the Full artifact, and its SHA-256 is:

```text
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

If you scroll down and **do not see `phase2A_RS1_HISTORICAL`**, click the circular refresh icon beside `/kaggle/working` once. Then scroll again.

Do **not** download the `phase2A_RS1_FULL_ARTIFACT.zip` again — that is the Full model you already safely saved.

---

## 12. User

i dont find phase2A_RS1_HISTORICAL_ARTIFACT

## 12. Assistant

That is okay — since H3 itself printed that the ZIP was successfully created, this is most likely a **Kaggle file-panel refresh/display issue**, not a missing artifact.

Run this **small verification cell now** in the same Kaggle session:

```python
from pathlib import Path

hist_dir = Path("/kaggle/working/phase2A_RS1_HISTORICAL")
hist_zip = hist_dir / "phase2A_RS1_HISTORICAL_ARTIFACT.zip"

print("Historical folder exists:", hist_dir.exists())
print("Historical ZIP exists   :", hist_zip.exists())

if hist_dir.exists():
    print("\nContents:")
    for p in hist_dir.iterdir():
        print(" -", p.name)
```

You should see:

```text
Historical folder exists: True
Historical ZIP exists   : True
```

If it says **True**, then make an easy-to-see copy directly under `/kaggle/working`:

```python
import shutil
from pathlib import Path

src = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL/"
    "phase2A_RS1_HISTORICAL_ARTIFACT.zip"
)

dst = Path("/kaggle/working/HISTORICAL_ARTIFACT_DOWNLOAD_ME.zip")

assert src.exists()

shutil.copy2(src, dst)

print("Copied to:", dst)
print("Size:", round(dst.stat().st_size / (1024**2), 2), "MB")
```

This **does not change the trained model or original artifact**. It only makes an identical copy at the top level so Kaggle's file browser can show it more easily.

Then click the **refresh icon beside `/kaggle/working`** in the right panel.

You should then see:

```text
HISTORICAL_ARTIFACT_DOWNLOAD_ME.zip
```

Download that file.

Its SHA must still be:

```text
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

Run the first verification cell and send me what it prints.

---

## 13. User

```text
Historical folder exists: True
Historical ZIP exists   : True

Contents:
 - phase2A_RS1_HISTORICAL_environment.json
 - phase2A_RS1_HISTORICAL_ARTIFACT.zip
 - phase2A_RS1_HISTORICAL_ARTIFACT
 - phase2A_RS1_HISTORICAL_ARTIFACT.zip.sha256.txt
 - phase2A_RS1_HISTORICAL_training_origin_manifest.json
 - phase2A_RS1_HISTORICAL_READY_TO_EXPORT.txt
 - phase2A_RS1_HISTORICAL_refit_contract.json
```

## 13. Assistant

Great — the Historical artifact is definitely there. The issue is only Kaggle’s file browser display.

Now make a top-level copy so it’s easy to download:

```python
import shutil
from pathlib import Path

src = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL/"
    "phase2A_RS1_HISTORICAL_ARTIFACT.zip"
)

dst = Path("/kaggle/working/HISTORICAL_ARTIFACT_DOWNLOAD_ME.zip")

shutil.copy2(src, dst)

print("Copied to:", dst)
print("Size:", round(dst.stat().st_size / (1024**2), 2), "MB")
```

Then click the refresh icon next to `/kaggle/working` in the right panel. You should see:

```text
HISTORICAL_ARTIFACT_DOWNLOAD_ME.zip
```

Download that file.

After downloading, verify it in Windows PowerShell:

```powershell
Get-FileHash "$HOME\Downloads\HISTORICAL_ARTIFACT_DOWNLOAD_ME.zip" -Algorithm SHA256
```

It must equal:

```text
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

Once that matches, both Full and Historical recovery artifacts are safely preserved outside Kaggle, and we can move on to frozen held-out inference.

---

## 14. User

its not downloading , as i am trying couple of times

## 14. Assistant

Since the ZIP is about **711 MB**, Kaggle’s browser download can sometimes fail on a large working-file download. We can avoid that completely by splitting the ZIP into smaller pieces, downloading those, and recombining them on your computer. This does **not** alter the trained model or the original ZIP.

Run this in Kaggle:

```python
from pathlib import Path
import hashlib

src = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL/"
    "phase2A_RS1_HISTORICAL_ARTIFACT.zip"
)

assert src.exists()

CHUNK_SIZE = 100 * 1024 * 1024  # 100 MB
prefix = "/kaggle/working/HISTORICAL_PART_"

parts = []

with open(src, "rb") as f:
    i = 1
    while True:
        chunk = f.read(CHUNK_SIZE)
        if not chunk:
            break

        p = Path(f"{prefix}{i:02d}.bin")
        with open(p, "wb") as out:
            out.write(chunk)

        sha = hashlib.sha256(chunk).hexdigest()
        parts.append((p.name, len(chunk), sha))
        print(p.name, round(len(chunk)/(1024**2), 2), "MB", sha)

        i += 1

print("\nTotal parts:", len(parts))
print("Original ZIP size:", round(src.stat().st_size/(1024**2), 2), "MB")
```

You should get roughly **8 smaller files**, something like:

```text
HISTORICAL_PART_01.bin
HISTORICAL_PART_02.bin
...
HISTORICAL_PART_08.bin
```

Then refresh `/kaggle/working` and download each part individually. A 100 MB file should be much easier for Kaggle to download than the 711 MB ZIP.

Once all parts are in your Windows **Downloads** folder, open PowerShell and run:

```powershell
$parts = Get-ChildItem "$HOME\Downloads\HISTORICAL_PART_*.bin" | Sort-Object Name

$out = "$HOME\Downloads\phase2A_RS1_HISTORICAL_ARTIFACT.zip"

$dest = [System.IO.File]::Create($out)

foreach ($part in $parts) {
    $src = [System.IO.File]::OpenRead($part.FullName)
    $src.CopyTo($dest)
    $src.Close()
}

$dest.Close()

Write-Host "Recombined file created:"
Write-Host $out
```

Then verify the recombined ZIP:

```powershell
Get-FileHash "$HOME\Downloads\phase2A_RS1_HISTORICAL_ARTIFACT.zip" -Algorithm SHA256
```

It **must** equal:

```text
C23F0BBC86B483BC267CBA8E186A876160E3DC1C5E40490F72D17E9BE389966B
```

If that matches, the reconstructed file on your computer is byte-for-byte identical to the original Historical artifact.

For now, run the **splitting cell only** and show me its output. Do not close the Kaggle session yet.

---

## 15. User

```text
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          C23F0BBC86B483BC267CBA8E186A876160E3DC1C5E40490F72D17E9BE389966B       C:\Users\Shahriar Habib\Downl...


PS C:\Users\Shahriar Habib>
```

## 15. Assistant

Perfect — the SHA-256 matches exactly.

Your downloaded Historical artifact is therefore **byte-for-byte identical** to the Kaggle original:

```text
C23F0BBC86B483BC267CBA8E186A876160E3DC1C5E40490F72D17E9BE389966B
```

So both RS-1 models are now safely preserved outside Kaggle:

```text
FULL
12962bd779ab9523d24736af2c68823ac66d41c56334261d7341d31991c8e545

HISTORICAL
c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b
```

This closes **RS-4F and RS-4H**. Do not retrain either model.

You can now safely close this Kaggle runtime. Keep the two verified ZIPs as your archival master copies; if you created temporary `.bin` pieces for the Historical ZIP, you can delete those after confirming the recombined ZIP opens normally.

Our next stage is **one-time frozen held-out inference on Regimes A–D**. We will load these saved Full and Historical artifacts, perform **no training**, and immediately save and hash row-level predictions/logits so the prediction evidence cannot be lost again.

---

## 16. User

how far we close 2A

## 16. Assistant

We are **very close to closing Phase 2A**.

At this point I would estimate Phase 2A as roughly **80–85% complete overall**, and about **95% of the expensive model-training work is finished**.

What is already closed:
- Classical ML Phase 1 baselines and frozen Regimes A–D
- Original AUTH-1 DeBERTa results documented
- Full RS-1 recovery model trained and externally checksum-verified
- Historical RS-1 recovery model trained and externally checksum-verified
- Deterministic FP32 implementation established
- Permanent memory-safe `batch 2 × accumulation 16 = effective 32` solution established
- Exact Full/Historical training-origin fingerprints recovered
- Both model artifacts now safely preserved; **no more DeBERTa training is required**

What remains before I would call **Phase 2A completely closed** is essentially four jobs:

1. **One-time frozen held-out inference**
   - Full RS-1 model → Regimes A and B
   - Historical RS-1 model → Regimes C and D
   - Save `reviewID`, `reviewerID`, `y_true`, predictions and logits/probabilities
   - Hash and externally preserve those prediction files immediately

2. **Reconstruct/freeze the corresponding classical row-level predictions**
   - Text-equivalent comparator
   - Strongest classical/behaviour comparator
   - Preserve the known exact/non-exact reconstruction status rather than altering anything

3. **Run the final paired statistical analysis — Cell 5D**
   - Reviewer-cluster bootstrap: 2,000
   - Paired reviewer-cluster permutation: 5,000
   - Eight comparisons
   - Holm correction across all eight
   - This gives the formal statistical sensitivity/reproducibility analysis for RS-1

4. **Final Phase-2A freeze**
   - Final tables
   - confusion matrices/class metrics
   - RQ1/H1 conclusion
   - AUTH-1 vs RS-1 distinction
   - reproducibility caveat
   - final SHA registry/manifest
   - dissertation-ready wording

Conceptually we are here:

```text
Phase 2A
│
├── Dataset/regime freeze                 ✅
├── Classical baselines                   ✅
├── Original AUTH-1 DeBERTa evaluation    ✅
├── Reproducibility investigation         ✅
├── RS-1 deterministic implementation     ✅
├── RS-1 Full final model                  ✅
├── RS-1 Historical final model            ✅
├── External artifact preservation         ✅
│
├── RS-1 held-out predictions              ← NEXT
├── Classical row-level recovery           ⏳
├── Paired statistical inference           ⏳
└── Final Phase-2A result freeze            ⏳
```

The important thing is that the **risky and time-consuming part is now behind us**. We do not need another multi-hour training experiment. The remaining work is mainly inference, statistical testing, artifact preservation and final interpretation.

Assuming the prediction pipeline behaves normally, I would expect us to **finish Phase 2A in the next working session**, rather than needing another several days.

After that, we can formally say:

> **Phase 2A — Yelp controlled RQ1 analysis: CLOSED**

and move directly to **Phase 2B: Dataset 2 audit and tripartite AI-fake / human-fake / genuine analysis**.

---

## 17. User

thanks lets move to the next

## 17. Assistant — Generated H4 Historical C/D Inference Cell

The assistant generated a dedicated Python cell/file for the next step, **RS-1 Historical frozen held-out inference on Regimes C and D**, designed to reload the saved Historical artifact, fingerprint the regimes, perform one-time inference, preserve row-level predictions/logits/probabilities, compute descriptive metrics, and create a hashed prediction ZIP.

```python
# =============================================================================
# H4 — RS-1 HISTORICAL FROZEN HELD-OUT INFERENCE: REGIMES C + D
# RUN ONCE, ONLY AFTER RS-4H ARTIFACT HAS BEEN EXTERNALLY SHA-256 VERIFIED
#
# This cell:
#   1) reconstructs and fingerprints C/D from the already-audited train origin,
#   2) verifies the frozen RS-4H artifact byte-for-byte,
#   3) RELOADS the saved model (does not use the live training model),
#   4) predicts C/D once with argmax(logits), no tuning,
#   5) saves row-level logits/probabilities and metrics,
#   6) creates a hashed, downloadable prediction ZIP.
#
# It does NOT train, refit, tune thresholds, or select a model.
# =============================================================================

import os
import gc
import json
import hashlib
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    f1_score,
    accuracy_score,
    balanced_accuracy_score,
    recall_score,
    precision_score,
    confusion_matrix,
)

print("=" * 100)
print("H4 — RS-1 HISTORICAL FROZEN HELD-OUT INFERENCE: REGIMES C + D")
print("=" * 100)

# -------------------------------------------------------------------------
# 0. Hard governance gates
# -------------------------------------------------------------------------
assert "train_full" in globals(), "H1 state missing: train_full"
assert "train_temporal" in globals(), "H1 state missing: train_temporal"
assert "HIST_FP" in globals(), "H1 state missing: HIST_FP"
assert "TEMPORAL_CUTOFF" in globals(), "H1 state missing: TEMPORAL_CUTOFF"

TARGET = "flagged"
TEXT_COL = "reviewContent"

EXPECTED_HIST_ORIGIN_FP = (
    "ed4e3a55e0c52f8949873847ba44ac8bebe8de77efd96daacc4cb4c5e592ea2e"
)
EXPECTED_REGIME_FP = {
    "C": "937867e10267f8b4ac6ce66bb4e6a85ad95b13b9a200763cc688b37b2c5152c6",
    "D": "4fe642b0f285a75c520eac8c8d168fe016ddcfbde511be99381491c3ef866543",
}
EXPECTED_N = {"C": 4324, "D": 4008}
EXPECTED_REVIEWERS = {"C": 3867, "D": 3641}
EXPECTED_CLASS_COUNTS = {
    "C": {0: 2237, 1: 2087},
    "D": {0: 1946, 1: 2062},
}

EXPECTED_HIST_ZIP_SHA256 = (
    "c23f0bbc86b483bc267cba8e186a876160e3dc1c5e40490f72d17e9be389966b"
)
EXPECTED_REGISTRY_SHA256 = (
    "63d93758880e8e53318a33de2c882fc492f994ec329c8bc9d96ff4ac299868fb"
)
EXPECTED_ARTIFACT_MANIFEST_SHA256 = (
    "692a2dc35b46a0c2797ed0667ab9c556f4ebf3e020b403ed3724dcfee087020a"
)
EXPECTED_FINAL_MODEL_SHA256 = (
    "ef4f18684c2f6bb7ad73ceed45ef48f8d7bb7f8ca0d0631c2324a37887233898"
)

ARTIFACT_ROOT = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL/"
    "phase2A_RS1_HISTORICAL_ARTIFACT"
)
HIST_ZIP = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL/"
    "phase2A_RS1_HISTORICAL_ARTIFACT.zip"
)
MODEL_DIR = ARTIFACT_ROOT / "model"

OUT_ROOT = Path("/kaggle/working/phase2A_RS1_HISTORICAL_CD_INFERENCE")
STAGING = Path(str(OUT_ROOT) + ".staging")
ZIP_OUT = Path("/kaggle/working/phase2A_RS1_HISTORICAL_CD_PREDICTIONS.zip")
ZIP_SHA_OUT = Path(
    "/kaggle/working/phase2A_RS1_HISTORICAL_CD_PREDICTIONS.zip.sha256.txt"
)

# A completed output is an intentional one-pass lock.
if OUT_ROOT.exists() or ZIP_OUT.exists():
    raise RuntimeError(
        "Historical C/D inference output already exists. "
        "Do NOT re-predict. Preserve the existing output instead."
    )

if STAGING.exists():
    raise RuntimeError(
        f"Incomplete staging directory exists: {STAGING}\n"
        "Stop and inspect it before deciding whether a rerun is justified."
    )

assert HIST_FP == EXPECTED_HIST_ORIGIN_FP
assert ARTIFACT_ROOT.is_dir(), f"Artifact directory missing: {ARTIFACT_ROOT}"
assert MODEL_DIR.is_dir(), f"Saved model directory missing: {MODEL_DIR}"
assert HIST_ZIP.is_file(), f"Historical ZIP missing: {HIST_ZIP}"
assert torch.cuda.is_available(), "GPU required for DeBERTa inference"

# -------------------------------------------------------------------------
# 1. Hash helpers
# -------------------------------------------------------------------------
def file_sha256(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()

def canonical_json_sha(payload):
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def content_fingerprint(df):
    cols = ["reviewID", "reviewerID", "flagged", "reviewContent"]
    for col in cols:
        assert col in df.columns
    assert df["reviewID"].notna().all()
    assert df["reviewerID"].notna().all()
    assert df["reviewContent"].notna().all()
    assert df["flagged"].isin([0, 1]).all()

    x = df[cols].copy()
    x["reviewID"] = x["reviewID"].astype(str)
    x["reviewerID"] = x["reviewerID"].astype(str)
    x["flagged"] = x["flagged"].astype(int)
    x["reviewContent"] = x["reviewContent"].astype(str)
    x = x.sort_values("reviewID", kind="mergesort").reset_index(drop=True)

    payload = json.dumps(
        x.to_dict(orient="records"),
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def whole_model_sha256(model):
    h = hashlib.sha256()
    with torch.no_grad():
        for name, param in model.named_parameters():
            arr = (
                param.detach()
                .to(dtype=torch.float32, device="cpu")
                .contiguous()
                .numpy()
            )
            h.update(name.encode("utf-8"))
            h.update(str(tuple(arr.shape)).encode("utf-8"))
            h.update(arr.tobytes(order="C"))
    return h.hexdigest()

def atomic_write_json(payload, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(destination.parent),
        prefix=destination.name + ".",
        suffix=".tmp",
    )
    os.close(fd)
    tmp = Path(tmp)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destination)
    finally:
        if tmp.exists():
            tmp.unlink()

# -------------------------------------------------------------------------
# 2. Reconstruct the exact frozen Historical regimes
# -------------------------------------------------------------------------
regime_C = (
    train_full.loc[train_full["date"] >= TEMPORAL_CUTOFF]
    .copy()
    .reset_index(drop=True)
)

historical_reviewers = set(train_temporal["reviewerID"].dropna())

regime_D = (
    regime_C.loc[
        ~regime_C["reviewerID"].isin(historical_reviewers)
    ]
    .copy()
    .reset_index(drop=True)
)

REGIMES = {"C": regime_C, "D": regime_D}

for r, df in REGIMES.items():
    assert len(df) == EXPECTED_N[r], (
        f"Regime {r}: expected {EXPECTED_N[r]}, got {len(df)}"
    )
    assert df["reviewID"].astype(str).nunique() == len(df)
    assert df["reviewerID"].nunique() == EXPECTED_REVIEWERS[r]
    assert int((df[TARGET] == 0).sum()) == EXPECTED_CLASS_COUNTS[r][0]
    assert int((df[TARGET] == 1).sum()) == EXPECTED_CLASS_COUNTS[r][1]

    fp = content_fingerprint(df)
    assert fp == EXPECTED_REGIME_FP[r], (
        f"Regime {r} fingerprint mismatch:\n{fp}"
    )

assert set(regime_D["reviewID"].astype(str)).issubset(
    set(regime_C["reviewID"].astype(str))
)

print("\nFrozen regimes verified:")
for r, df in REGIMES.items():
    print(
        f"  {r}: N={len(df):,} | reviewers={df['reviewerID'].nunique():,} "
        f"| G={(df[TARGET] == 0).sum():,} | F={(df[TARGET] == 1).sum():,} "
        f"| SHA={EXPECTED_REGIME_FP[r]}"
    )

# -------------------------------------------------------------------------
# 3. Verify frozen artifact before loading it
# -------------------------------------------------------------------------
observed_zip_sha = file_sha256(HIST_ZIP)
assert observed_zip_sha == EXPECTED_HIST_ZIP_SHA256, (
    f"Historical artifact ZIP SHA mismatch:\n{observed_zip_sha}"
)

registry_path = ARTIFACT_ROOT / "refit_registry.json"
manifest_path = ARTIFACT_ROOT / "artifact_manifest.json"

with open(registry_path, "r", encoding="utf-8") as f:
    registry = json.load(f)

registry_declared_sha = registry["payload_sha256"]
registry_payload = dict(registry)
registry_payload.pop("payload_sha256")
registry_recomputed_sha = canonical_json_sha(registry_payload)

assert registry_declared_sha == EXPECTED_REGISTRY_SHA256
assert registry_recomputed_sha == EXPECTED_REGISTRY_SHA256
assert registry["origin"] == "Historical"
assert registry["training_n"] == 5602
assert registry["origin_fingerprint"] == EXPECTED_HIST_ORIGIN_FP
assert registry["heldout_accessed"] is False
assert registry["validation_used"] is False
assert registry["final_model_parameter_sha256"] == EXPECTED_FINAL_MODEL_SHA256

with open(manifest_path, "r", encoding="utf-8") as f:
    artifact_manifest = json.load(f)

manifest_declared_sha = artifact_manifest["payload_sha256"]
manifest_payload = dict(artifact_manifest)
manifest_payload.pop("payload_sha256")
manifest_recomputed_sha = canonical_json_sha(manifest_payload)

assert manifest_declared_sha == EXPECTED_ARTIFACT_MANIFEST_SHA256
assert manifest_recomputed_sha == EXPECTED_ARTIFACT_MANIFEST_SHA256
assert artifact_manifest["registry_payload_sha256"] == EXPECTED_REGISTRY_SHA256
assert artifact_manifest["final_model_parameter_sha256"] == EXPECTED_FINAL_MODEL_SHA256

# Verify every file recorded in the artifact manifest.
for rec in artifact_manifest["files"]:
    p = ARTIFACT_ROOT / rec["path"]
    assert p.is_file(), f"Artifact file missing: {rec['path']}"
    assert p.stat().st_size == rec["size_bytes"]
    observed = file_sha256(p)
    assert observed == rec["sha256"], (
        f"Artifact file SHA mismatch: {rec['path']}"
    )

print("\nFrozen Historical artifact verified:")
print(f"  ZIP SHA256      : {observed_zip_sha}")
print(f"  Registry SHA256 : {registry_recomputed_sha}")
print(f"  Manifest SHA256 : {manifest_recomputed_sha}")

# -------------------------------------------------------------------------
# 4. Free training objects, then RELOAD saved artifact model
# -------------------------------------------------------------------------
for obj_name in [
    "model", "optimizer", "scheduler", "encoded",
    "dataset", "loader", "tokenizer"
]:
    if obj_name in globals():
        del globals()[obj_name]

gc.collect()
torch.cuda.empty_cache()

DEVICE = torch.device("cuda")
INFERENCE_BATCH = 16
MAX_LENGTH = int(registry["max_length"])
assert MAX_LENGTH == 256

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR,
    dtype=torch.float32,
).to(device=DEVICE, dtype=torch.float32)

model.eval()
assert {p.dtype for p in model.parameters()} == {torch.float32}

reloaded_model_sha = whole_model_sha256(model)
assert reloaded_model_sha == EXPECTED_FINAL_MODEL_SHA256, (
    "Reloaded model parameter SHA mismatch:\n"
    f"{reloaded_model_sha}"
)

print(f"\nReloaded saved-model SHA256: {reloaded_model_sha}")
print(f"Inference batch            : {INFERENCE_BATCH}")
print("Prediction rule            : argmax(logits)")
print("Threshold tuning           : False")

# -------------------------------------------------------------------------
# 5. Deterministic inference helper
# -------------------------------------------------------------------------
class EncodedTextDataset(Dataset):
    def __init__(self, encodings):
        self.encodings = encodings
        self.n = int(encodings["input_ids"].shape[0])

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        return {k: v[idx] for k, v in self.encodings.items()}

def predict_regime(df, regime):
    texts = df[TEXT_COL].astype(str).tolist()

    enc = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    ds = EncodedTextDataset(enc)
    loader = DataLoader(
        ds,
        batch_size=INFERENCE_BATCH,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )

    logits_parts = []

    with torch.inference_mode():
        for step, batch in enumerate(loader, start=1):
            batch = {
                k: v.to(DEVICE, non_blocking=False)
                for k, v in batch.items()
            }
            logits = model(**batch).logits
            assert torch.isfinite(logits).all()
            logits_parts.append(
                logits.detach().to(dtype=torch.float32, device="cpu")
            )

            if step % 50 == 0 or step == len(loader):
                print(
                    f"  Regime {regime}: batch {step:03d}/{len(loader):03d}"
                )

    logits = torch.cat(logits_parts, dim=0)
    assert logits.shape == (len(df), 2)

    probs = F.softmax(logits, dim=1)
    pred = torch.argmax(logits, dim=1)

    out = pd.DataFrame({
        "reviewID": df["reviewID"].to_numpy(),
        "reviewerID": df["reviewerID"].to_numpy(),
        "regime": regime,
        "origin": "Historical",
        "y_true": df[TARGET].astype(int).to_numpy(),
        "y_pred": pred.numpy().astype(np.int64),
        "logit_0": logits[:, 0].numpy().astype(np.float32),
        "logit_1": logits[:, 1].numpy().astype(np.float32),
        "prob_genuine": probs[:, 0].numpy().astype(np.float32),
        "prob_fake": probs[:, 1].numpy().astype(np.float32),
    })

    assert len(out) == len(df)
    assert out["reviewID"].astype(str).tolist() == (
        df["reviewID"].astype(str).tolist()
    )
    assert out["reviewerID"].astype(str).tolist() == (
        df["reviewerID"].astype(str).tolist()
    )
    assert np.array_equal(
        out["y_true"].to_numpy(),
        df[TARGET].astype(int).to_numpy(),
    )
    assert out["y_pred"].isin([0, 1]).all()
    assert np.isfinite(
        out[["logit_0", "logit_1", "prob_genuine", "prob_fake"]]
        .to_numpy()
    ).all()
    assert np.allclose(
        out["prob_genuine"].to_numpy() + out["prob_fake"].to_numpy(),
        1.0,
        atol=1e-6,
    )

    return out

print("\nStarting one-time frozen inference...")
pred_C = predict_regime(regime_C, "C")
pred_D = predict_regime(regime_D, "D")

# Disable further intentional prediction calls in this cell's workflow.
ALLOW_HELDOUT_REPREDICTION = False

# -------------------------------------------------------------------------
# 6. Descriptive metrics — no selection/tuning
# -------------------------------------------------------------------------
def metrics_for(pred_df, regime):
    y = pred_df["y_true"].to_numpy()
    p = pred_df["y_pred"].to_numpy()

    cm = confusion_matrix(y, p, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    return {
        "regime": regime,
        "origin": "Historical",
        "n": int(len(pred_df)),
        "n_reviewers": int(pred_df["reviewerID"].nunique()),
        "macro_f1": float(f1_score(y, p, average="macro")),
        "accuracy": float(accuracy_score(y, p)),
        "balanced_accuracy": float(balanced_accuracy_score(y, p)),
        "genuine_precision": float(
            precision_score(y, p, labels=[0], average=None, zero_division=0)[0]
        ),
        "genuine_recall": float(
            recall_score(y, p, labels=[0], average=None, zero_division=0)[0]
        ),
        "genuine_f1": float(
            f1_score(y, p, labels=[0], average=None, zero_division=0)[0]
        ),
        "fake_precision": float(
            precision_score(y, p, labels=[1], average=None, zero_division=0)[0]
        ),
        "fake_recall": float(
            recall_score(y, p, labels=[1], average=None, zero_division=0)[0]
        ),
        "fake_f1": float(
            f1_score(y, p, labels=[1], average=None, zero_division=0)[0]
        ),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }

metrics_C = metrics_for(pred_C, "C")
metrics_D = metrics_for(pred_D, "D")
metrics_df = pd.DataFrame([metrics_C, metrics_D])

print("\nDescriptive RS-1 Historical metrics:")
for m in [metrics_C, metrics_D]:
    print(
        f"  {m['regime']}: Macro-F1={m['macro_f1']:.4f} | "
        f"TN={m['tn']} FP={m['fp']} FN={m['fn']} TP={m['tp']}"
    )

# -------------------------------------------------------------------------
# 7. Atomic output bundle + SHA registry
# -------------------------------------------------------------------------
STAGING.mkdir(parents=False, exist_ok=False)

c_path = STAGING / "RS1_Historical_Regime_C_predictions.csv"
d_path = STAGING / "RS1_Historical_Regime_D_predictions.csv"
combined_path = STAGING / "RS1_Historical_CD_predictions.csv"
metrics_path = STAGING / "RS1_Historical_CD_metrics.csv"

pred_C.to_csv(c_path, index=False, float_format="%.9g")
pred_D.to_csv(d_path, index=False, float_format="%.9g")
pd.concat([pred_C, pred_D], ignore_index=True).to_csv(
    combined_path,
    index=False,
    float_format="%.9g",
)
metrics_df.to_csv(metrics_path, index=False, float_format="%.12g")

output_files = {
    "regime_C_predictions": {
        "name": c_path.name,
        "n_rows": int(len(pred_C)),
        "sha256": file_sha256(c_path),
    },
    "regime_D_predictions": {
        "name": d_path.name,
        "n_rows": int(len(pred_D)),
        "sha256": file_sha256(d_path),
    },
    "combined_CD_predictions": {
        "name": combined_path.name,
        "n_rows": int(len(pred_C) + len(pred_D)),
        "sha256": file_sha256(combined_path),
    },
    "metrics": {
        "name": metrics_path.name,
        "n_rows": 2,
        "sha256": file_sha256(metrics_path),
    },
}

inference_registry = {
    "phase": "Phase 2A",
    "analysis_role": "RS-1 recovery/sensitivity held-out inference",
    "auth1_primary_results_replaced": False,
    "origin": "Historical",
    "model_artifact_zip_sha256": observed_zip_sha,
    "model_registry_sha256": registry_recomputed_sha,
    "artifact_manifest_sha256": manifest_recomputed_sha,
    "model_parameter_sha256": reloaded_model_sha,
    "max_length": MAX_LENGTH,
    "inference_precision": "FP32",
    "inference_batch": INFERENCE_BATCH,
    "prediction_rule": "argmax(logits)",
    "threshold_tuning": False,
    "model_selection": False,
    "training_performed": False,
    "regimes": {
        "C": {
            "n": EXPECTED_N["C"],
            "n_reviewers": EXPECTED_REVIEWERS["C"],
            "fingerprint": EXPECTED_REGIME_FP["C"],
        },
        "D": {
            "n": EXPECTED_N["D"],
            "n_reviewers": EXPECTED_REVIEWERS["D"],
            "fingerprint": EXPECTED_REGIME_FP["D"],
        },
    },
    "outputs": output_files,
    "metrics": {
        "C": metrics_C,
        "D": metrics_D,
    },
}
inference_registry["payload_sha256"] = canonical_json_sha(inference_registry)

registry_out = STAGING / "RS1_Historical_CD_inference_registry.json"
atomic_write_json(inference_registry, registry_out)

# Add registry file SHA to a separate final manifest so the registry's own
# canonical payload hash remains stable.
final_manifest = {
    "status": "PASS",
    "origin": "Historical",
    "regimes": ["C", "D"],
    "inference_registry_payload_sha256": inference_registry["payload_sha256"],
    "files": [],
}

for p in sorted(x for x in STAGING.rglob("*") if x.is_file()):
    final_manifest["files"].append({
        "path": p.name,
        "size_bytes": int(p.stat().st_size),
        "sha256": file_sha256(p),
    })

final_manifest["payload_sha256"] = canonical_json_sha(final_manifest)
manifest_out = STAGING / "RS1_Historical_CD_output_manifest.json"
atomic_write_json(final_manifest, manifest_out)

# Finalise the directory atomically.
os.replace(STAGING, OUT_ROOT)

# Build a small download ZIP.
tmp_zip = Path(str(ZIP_OUT) + ".tmp")
with zipfile.ZipFile(
    tmp_zip,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    allowZip64=True,
) as zf:
    for p in sorted(x for x in OUT_ROOT.rglob("*") if x.is_file()):
        zf.write(p, arcname=str(Path(OUT_ROOT.name) / p.relative_to(OUT_ROOT)))

os.replace(tmp_zip, ZIP_OUT)
prediction_zip_sha = file_sha256(ZIP_OUT)

with open(ZIP_SHA_OUT, "w", encoding="utf-8") as f:
    f.write(f"{prediction_zip_sha}  {ZIP_OUT.name}\n")

print("\n" + "=" * 100)
print("H4 COMPLETE — HISTORICAL C/D PREDICTIONS FROZEN")
print("=" * 100)
print(f"Regime C prediction SHA256 : {output_files['regime_C_predictions']['sha256']}")
print(f"Regime D prediction SHA256 : {output_files['regime_D_predictions']['sha256']}")
print(f"Combined C/D SHA256        : {output_files['combined_CD_predictions']['sha256']}")
print(f"Inference registry SHA256  : {inference_registry['payload_sha256']}")
print(f"Output manifest SHA256     : {final_manifest['payload_sha256']}")
print(f"Prediction ZIP             : {ZIP_OUT}")
print(f"Prediction ZIP SHA256      : {prediction_zip_sha}")
print("\n✓ H4 PASSED")
print("✓ Saved model artifact was reloaded and parameter-hash verified")
print("✓ Regimes C/D were fingerprint-verified before inference")
print("✓ Row-level reviewID/reviewerID/labels/logits/probabilities were preserved")
print("✓ No training, threshold tuning, or model selection occurred")
print("\nSTOP. Download and locally SHA-256 verify the prediction ZIP before closing this runtime.")
```

The generated Python file was:

`/mnt/data/phase2A_RS1_H4_HISTORICAL_CD_INFERENCE_CELL.py`

---

## 18. User

did not find the Zip

---

## 19. User

Make a markdown file end-to-end chat thread of this from the begining to the end , all of it

---

# End of Transcript
