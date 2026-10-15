from pathlib import Path
import gc
import hashlib
import json
import os
import random
import sys
import zipfile

import numpy as np
import torch
import transformers
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer


WIDTH = 120
INPUT_ROOT = Path("/kaggle/input")
WORKING_ROOT = Path("/kaggle/working")
OUTPUT_ROOT = WORKING_ROOT / "phase2B_DEBERTA_V3_3CLASS_INITIALISED"
OUTPUT_ZIP = WORKING_ROOT / "phase2B_DEBERTA_V3_3CLASS_INITIALISED.zip"
OUTPUT_SIDECAR = WORKING_ROOT / "phase2B_DEBERTA_V3_3CLASS_INITIALISED.zip.sha256.txt"
MODEL_DIR = OUTPUT_ROOT / "model"

SEED = 42
EXPECTED_T2_MANIFEST_PAYLOAD = (
    "b87c3945e0b50df788801c14cb9fcb2c88bf569e7c4556d9bfc168f8eb18cba8"
)
EXPECTED_BASE_MANIFEST_PAYLOAD = (
    "da21152ffc73c474d53485d3c0673eb0869cd50894d937acd1a2feb79eb8f33c"
)
EXPECTED_BASE_ZIP_SHA256 = (
    "4b91307e1a73dec76723c8318dfe8af09b952a4dca428169ae4eaa7cc2ecb7a7"
)
EXPECTED_BASE_WEIGHT_SHA256 = (
    "691d48a2800b926a19e3051def466fc2cca4f59a15e42ce4a0cf7f1b380b5e33"
)
EXPECTED_REPOSITORY = "microsoft/deberta-v3-base"
EXPECTED_REVISION = "8ccc9b6f36199bec6961081d44eb72fb3f7353f3"

LABEL2ID = {
    "presumed_truthful": 0,
    "human_deceptive": 1,
    "ai_generated": 2,
}
ID2LABEL = {value: key for key, value in LABEL2ID.items()}


def require(condition, message):
    if not condition:
        raise RuntimeError("STOP — " + message)


def section(title):
    print("\n" + title)
    print("-" * WIDTH)


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parameter_sha256(model):
    """Hash names, dtypes, shapes and exact bytes of the complete state dict."""
    digest = hashlib.sha256()
    state = model.state_dict()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii"))
        digest.update(b"\0")
        digest.update(tensor.numpy().tobytes(order="C"))
        digest.update(b"\0")
    return digest.hexdigest()


def load_eligible_rows(t2_root):
    rows = []
    for role, filename, expected_n in (
        ("primary", "primary_tripartite_corpus.jsonl", 2396),
        ("llama_sensitivity", "llama_unseen_generator_sensitivity.jsonl", 790),
    ):
        path = t2_root / filename
        require(path.is_file(), f"missing frozen corpus file: {filename}")
        role_rows = []
        with path.open("r", encoding="utf-8", errors="strict") as handle:
            for line_number, line in enumerate(handle, start=1):
                record = json.loads(line)
                require(
                    isinstance(record.get("row_id"), str),
                    f"{filename}:{line_number} missing row_id",
                )
                require(
                    isinstance(record.get("text"), str),
                    f"{filename}:{line_number} missing text",
                )
                require(record["text"].strip() != "", f"{record['row_id']} has empty text")
                role_rows.append((role, record["row_id"], record["text"]))
        require(len(role_rows) == expected_n, f"{role} row count differs: {len(role_rows)}")
        rows.extend(role_rows)
    require(len(rows) == 3186, f"combined eligible row count differs: {len(rows)}")
    require(len({row_id for _, row_id, _ in rows}) == len(rows), "eligible row IDs are not unique")
    return rows


def tokenizer_backend_identity(tokenizer):
    backend = json.loads(tokenizer.backend_tokenizer.to_str())
    pretokenizer = backend.get("pre_tokenizer")
    require(pretokenizer is not None, "tokenizer backend has no pre-tokenizer")
    pretokenizer_json = json.dumps(
        pretokenizer,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    require("Metaspace" in pretokenizer_json, "native DeBERTa Metaspace pre-tokenizer is absent")
    require('"Split"' not in pretokenizer_json, "Mistral Split regex was applied to the DeBERTa tokenizer")
    return hashlib.sha256(pretokenizer_json.encode("utf-8")).hexdigest()


def token_id_fingerprint(tokenizer, rows):
    digest = hashlib.sha256()
    for _, row_id, text in rows:
        token_ids = tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
            return_attention_mask=False,
            return_token_type_ids=False,
            verbose=False,
        )["input_ids"]
        digest.update(row_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(json.dumps(token_ids, separators=(",", ":")).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def deterministic_zip(source_dir, destination):
    """Create a ZIP whose member order, timestamps and permissions are fixed."""
    base = source_dir.parent
    paths = sorted(path for path in source_dir.rglob("*") if path.is_file())
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in paths:
            arcname = path.relative_to(base).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


print("=" * WIDTH)
print("PHASE 2B — STEP M1C-B: DETERMINISTIC THREE-CLASS INITIALISATION AND PRESERVATION")
print("=" * WIDTH)
print("Python       :", sys.version.split()[0])
print("PyTorch      :", torch.__version__)
print("Transformers :", transformers.__version__)
print("Execution    : CPU-only initialisation; no training or inference")

require(INPUT_ROOT.is_dir(), "Kaggle input root is unavailable")
require(not torch.cuda.is_available(), "this preservation cell must run in the CPU-only session")
require(not OUTPUT_ROOT.exists(), f"output directory already exists: {OUTPUT_ROOT}")
require(not OUTPUT_ZIP.exists(), f"output ZIP already exists: {OUTPUT_ZIP}")
require(not OUTPUT_SIDECAR.exists(), f"output sidecar already exists: {OUTPUT_SIDECAR}")

section("FROZEN INPUT CONTINUITY")
t2_candidates = sorted(INPUT_ROOT.rglob("corpus_manifest.json"))
require(len(t2_candidates) == 1, f"expected one T2 manifest; found {len(t2_candidates)}")
T2_ROOT = t2_candidates[0].parent
t2_manifest = json.loads(t2_candidates[0].read_text(encoding="utf-8"))
require(
    t2_manifest.get("manifest_payload_sha256") == EXPECTED_T2_MANIFEST_PAYLOAD,
    "T2 manifest payload differs",
)
eligible_rows = load_eligible_rows(T2_ROOT)

base_manifest_candidates = sorted(INPUT_ROOT.rglob("checkpoint_manifest.json"))
require(
    len(base_manifest_candidates) == 1,
    f"expected one pinned-base manifest; found {len(base_manifest_candidates)}",
)
BASE_ROOT = base_manifest_candidates[0].parent
base_manifest = json.loads(base_manifest_candidates[0].read_text(encoding="utf-8"))
stored_base_payload = base_manifest.get("manifest_payload_sha256")
base_payload = {
    key: value for key, value in base_manifest.items()
    if key != "manifest_payload_sha256"
}
require(stored_base_payload == EXPECTED_BASE_MANIFEST_PAYLOAD, "stored base manifest payload differs")
require(canonical_sha256(base_payload) == EXPECTED_BASE_MANIFEST_PAYLOAD, "recomputed base manifest payload differs")
require(base_payload["source"]["repo_id"] == EXPECTED_REPOSITORY, "base repository differs")
require(base_payload["source"]["resolved_commit_sha"] == EXPECTED_REVISION, "base revision differs")
require(file_sha256(BASE_ROOT / "pytorch_model.bin") == EXPECTED_BASE_WEIGHT_SHA256, "base weight checksum differs")

sidecars = sorted(INPUT_ROOT.rglob("phase2B_DEBERTA_V3_BASE_PINNED.zip.sha256.txt"))
require(len(sidecars) == 1, f"expected one base ZIP sidecar; found {len(sidecars)}")
sidecar_tokens = sidecars[0].read_text(encoding="utf-8", errors="strict").strip().split()
require(sidecar_tokens and sidecar_tokens[0].lower() == EXPECTED_BASE_ZIP_SHA256, "base ZIP sidecar differs")

print("T2 manifest payload       :", EXPECTED_T2_MANIFEST_PAYLOAD)
print("Eligible texts verified   :", len(eligible_rows))
print("Base manifest payload     :", EXPECTED_BASE_MANIFEST_PAYLOAD)
print("Base repository           :", EXPECTED_REPOSITORY)
print("Base resolved revision    :", EXPECTED_REVISION)
print("Base weight SHA256        :", EXPECTED_BASE_WEIGHT_SHA256)
print("Externally verified ZIP   :", EXPECTED_BASE_ZIP_SHA256)

section("DETERMINISTIC INITIALISATION POLICY")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)

print("Seed                         :", SEED)
print("torch deterministic algorithms:", torch.are_deterministic_algorithms_enabled())
print("Torch threads                :", torch.get_num_threads())
print("Initialisation device        : CPU")
print("Initialisation dtype         : float32")
print("Label mapping                :", LABEL2ID)

section("LOCAL TOKENIZER AND THREE-CLASS MODEL INITIALISATION")
print("Tokenizer policy: retain DeBERTa's native Unigram + Metaspace pipeline.")
print("A known Transformers 5.0.0 false-positive Mistral warning may be emitted during the first local load.")
config = AutoConfig.from_pretrained(str(BASE_ROOT), local_files_only=True)
require(config.model_type == "deberta-v2", f"unexpected model_type: {config.model_type}")
config.num_labels = 3
config.id2label = ID2LABEL
config.label2id = LABEL2ID
config.problem_type = "single_label_classification"

tokenizer = AutoTokenizer.from_pretrained(
    str(BASE_ROOT),
    local_files_only=True,
)
initial_tokenizer_class = tokenizer.__class__.__name__
initial_tokenizer_is_fast = tokenizer.is_fast
initial_tokenizer_vocab_size = tokenizer.vocab_size
initial_special_ids = list(tokenizer.all_special_ids)
initial_pretokenizer_hash = tokenizer_backend_identity(tokenizer)
initial_token_id_hash = token_id_fingerprint(tokenizer, eligible_rows)

model, loading_info = AutoModelForSequenceClassification.from_pretrained(
    str(BASE_ROOT),
    config=config,
    local_files_only=True,
    output_loading_info=True,
)
model.to(device="cpu", dtype=torch.float32)
model.eval()

missing_keys = sorted(loading_info.get("missing_keys", []))
unexpected_keys = sorted(loading_info.get("unexpected_keys", []))
mismatched_keys = sorted(loading_info.get("mismatched_keys", []), key=str)
error_messages = loading_info.get("error_msgs", [])

allowed_missing_prefixes = ("classifier.", "pooler.")
allowed_unexpected_prefixes = ("lm_predictions.", "mask_predictions.")

require(missing_keys, "no newly initialised classification/pooler parameters were reported")
require(
    all(key.startswith(allowed_missing_prefixes) for key in missing_keys),
    f"unexpected missing base parameters: {missing_keys}",
)
require(
    any(key.startswith("classifier.") for key in missing_keys),
    "classification-head parameters were not reported as newly initialised",
)
require(
    all(key.startswith(allowed_unexpected_prefixes) for key in unexpected_keys),
    f"unexpected unused source parameters: {unexpected_keys}",
)
require(not mismatched_keys, f"mismatched parameters found: {mismatched_keys}")
require(not error_messages, f"loader errors found: {error_messages}")
require(model.config.num_labels == 3, "model does not have three output labels")
require(model.config.label2id == LABEL2ID, "saved model label2id mapping differs")
require(
    {int(key): value for key, value in model.config.id2label.items()} == ID2LABEL,
    "saved model id2label mapping differs",
)

floating_dtypes = {
    str(parameter.dtype)
    for parameter in model.parameters()
    if parameter.is_floating_point()
}
require(floating_dtypes == {"torch.float32"}, f"unexpected floating parameter dtypes: {floating_dtypes}")

parameter_count = sum(parameter.numel() for parameter in model.parameters())
trainable_parameter_count = sum(
    parameter.numel() for parameter in model.parameters() if parameter.requires_grad
)
initial_parameter_hash = parameter_sha256(model)

print("Model class                :", model.__class__.__name__)
print("Tokenizer class            :", tokenizer.__class__.__name__)
print("Tokenizer fast             :", tokenizer.is_fast)
print("Vocabulary size            :", tokenizer.vocab_size)
print("Tokenizer policy           : native DeBERTa Unigram + Metaspace; no Mistral regex patch")
print("Pre-tokenizer SHA256       :", initial_pretokenizer_hash)
print("3,186-row token-ID SHA256  :", initial_token_id_hash)
print("Missing/new parameters     :", missing_keys)
print("Unused pretraining params  :", unexpected_keys)
print("Mismatched parameters      :", mismatched_keys)
print("Parameter count            :", parameter_count)
print("Trainable parameter count  :", trainable_parameter_count)
print("Initial parameter SHA256   :", initial_parameter_hash)

section("ARTIFACT SAVE AND INDEPENDENT RELOAD")
MODEL_DIR.mkdir(parents=True, exist_ok=False)
model.config.architectures = [model.__class__.__name__]
model.save_pretrained(
    str(MODEL_DIR),
    safe_serialization=True,
    max_shard_size="5GB",
)
tokenizer.save_pretrained(str(MODEL_DIR))

del model
del tokenizer
gc.collect()

reloaded_tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_DIR),
    local_files_only=True,
)
reloaded_model = AutoModelForSequenceClassification.from_pretrained(
    str(MODEL_DIR),
    local_files_only=True,
)
reloaded_model.to(device="cpu", dtype=torch.float32)
reloaded_model.eval()
reloaded_parameter_hash = parameter_sha256(reloaded_model)
reloaded_pretokenizer_hash = tokenizer_backend_identity(reloaded_tokenizer)
reloaded_token_id_hash = token_id_fingerprint(reloaded_tokenizer, eligible_rows)

require(reloaded_parameter_hash == initial_parameter_hash, "parameter hash changed after save/reload")
require(reloaded_model.config.num_labels == 3, "reloaded model does not have three labels")
require(reloaded_model.config.label2id == LABEL2ID, "reloaded label2id differs")
require(
    {int(key): value for key, value in reloaded_model.config.id2label.items()} == ID2LABEL,
    "reloaded id2label differs",
)
require(reloaded_tokenizer.__class__.__name__ == initial_tokenizer_class, "reloaded tokenizer class differs")
require(reloaded_tokenizer.is_fast == initial_tokenizer_is_fast, "reloaded tokenizer backend differs")
require(reloaded_tokenizer.vocab_size == initial_tokenizer_vocab_size, "reloaded vocabulary size differs")
require(list(reloaded_tokenizer.all_special_ids) == initial_special_ids, "reloaded special-token IDs differ")
require(reloaded_pretokenizer_hash == initial_pretokenizer_hash, "pre-tokenizer changed after save/reload")
require(reloaded_token_id_hash == initial_token_id_hash, "eligible-corpus token IDs changed after save/reload")

print("Saved model format          : safetensors")
print("Reloaded model class        :", reloaded_model.__class__.__name__)
print("Reloaded tokenizer class    :", reloaded_tokenizer.__class__.__name__)
print("Reloaded parameter SHA256   :", reloaded_parameter_hash)
print("Reloaded pre-tokenizer SHA256:", reloaded_pretokenizer_hash)
print("Reloaded token-ID SHA256    :", reloaded_token_id_hash)
print("Save/reload identity        : PASS")

del reloaded_model
del reloaded_tokenizer
gc.collect()

section("FROZEN INITIALISATION ARTIFACT")
model_files = sorted(path for path in MODEL_DIR.rglob("*") if path.is_file())
require(model_files, "no model artifact files were saved")

model_registry = {
    path.relative_to(OUTPUT_ROOT).as_posix(): {
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }
    for path in model_files
}

manifest_payload = {
    "phase": "Phase 2B",
    "step": "M1C-B",
    "status": "FROZEN_THREE_CLASS_INITIALISATION",
    "upstream": {
        "t2_manifest_payload_sha256": EXPECTED_T2_MANIFEST_PAYLOAD,
        "base_checkpoint_manifest_payload_sha256": EXPECTED_BASE_MANIFEST_PAYLOAD,
        "base_checkpoint_zip_sha256": EXPECTED_BASE_ZIP_SHA256,
        "base_weight_sha256": EXPECTED_BASE_WEIGHT_SHA256,
        "repository": EXPECTED_REPOSITORY,
        "resolved_revision": EXPECTED_REVISION,
    },
    "environment": {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": "cpu",
        "dtype": "float32",
    },
    "initialisation": {
        "seed": SEED,
        "torch_deterministic_algorithms": True,
        "torch_threads": 1,
        "model_class": "DebertaV2ForSequenceClassification",
        "num_labels": 3,
        "label2id": LABEL2ID,
        "id2label": {str(key): value for key, value in ID2LABEL.items()},
        "problem_type": "single_label_classification",
        "newly_initialised_keys": missing_keys,
        "unused_pretraining_keys": unexpected_keys,
        "mismatched_keys": mismatched_keys,
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "parameter_sha256": initial_parameter_hash,
        "tokenizer_class": initial_tokenizer_class,
        "tokenizer_is_fast": initial_tokenizer_is_fast,
        "tokenizer_vocab_size": initial_tokenizer_vocab_size,
        "tokenizer_policy": "native_deberta_unigram_metaspace_no_mistral_regex_patch",
        "tokenizer_policy_reason": (
            "Transformers 5.0.0 emits a false-positive Mistral-regex warning for the local "
            "versionless DeBERTa config with vocabulary above 100,000; the model is DeBERTa, "
            "so its native Metaspace pre-tokenizer is retained."
        ),
        "eligible_texts_tokenised": len(eligible_rows),
        "pretokenizer_sha256": initial_pretokenizer_hash,
        "eligible_corpus_token_ids_sha256": initial_token_id_hash,
        "tokenizer_save_reload_identity": True,
    },
    "artifact_files": model_registry,
    "training_performed": False,
    "inference_performed": False,
}
manifest_payload_hash = canonical_sha256(manifest_payload)
manifest = dict(manifest_payload)
manifest["manifest_payload_sha256"] = manifest_payload_hash
manifest_path = OUTPUT_ROOT / "initialisation_manifest.json"
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

checksum_targets = sorted(
    path for path in OUTPUT_ROOT.rglob("*")
    if path.is_file() and path.name != "SHA256SUMS.txt"
)
checksum_lines = [
    f"{file_sha256(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}"
    for path in checksum_targets
]
checksum_path = OUTPUT_ROOT / "SHA256SUMS.txt"
checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

for path in sorted(path for path in OUTPUT_ROOT.rglob("*") if path.is_file()):
    print(
        f"{path.relative_to(OUTPUT_ROOT).as_posix():48s} "
        f"{path.stat().st_size:12d} bytes  {file_sha256(path)}"
    )

deterministic_zip(OUTPUT_ROOT, OUTPUT_ZIP)
zip_hash = file_sha256(OUTPUT_ZIP)
OUTPUT_SIDECAR.write_text(f"{zip_hash}  {OUTPUT_ZIP.name}\n", encoding="utf-8")

print("Initialisation manifest payload SHA256:", manifest_payload_hash)
print("Initial parameter SHA256              :", initial_parameter_hash)

print("\n" + "=" * WIDTH)
print("STEP M1C-B DECISION: THREE-CLASS INITIALISATION FROZEN AND RELOAD-VERIFIED")
print("=" * WIDTH)
print("Output directory :", OUTPUT_ROOT)
print("Artifact ZIP     :", OUTPUT_ZIP)
print("ZIP SHA256       :", zip_hash)
print("Checksum sidecar :", OUTPUT_SIDECAR)
print("Training         : NONE")
print("Inference        : NONE")
print("Download the ZIP and .sha256.txt, then verify the ZIP externally.")
print("STOP — share this complete output before the model/hyperparameter contract is frozen.")
