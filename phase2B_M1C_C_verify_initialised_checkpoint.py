from pathlib import Path
import hashlib
import json
import sys


WIDTH = 120
INPUT_ROOT = Path("/kaggle/input")

EXPECTED_T2_PAYLOAD = (
    "b87c3945e0b50df788801c14cb9fcb2c88bf569e7c4556d9bfc168f8eb18cba8"
)
EXPECTED_BASE_PAYLOAD = (
    "da21152ffc73c474d53485d3c0673eb0869cd50894d937acd1a2feb79eb8f33c"
)
EXPECTED_INITIALISATION_PAYLOAD = (
    "171154b7225ded4b88d0024a5ba20e2314bee3213dc0d16c3575a40bec13fd45"
)
EXPECTED_ZIP_SHA256 = (
    "e392a33112c5d8e94a1635bb1096d689cda41f40a69af55a319a125ad361613a"
)
EXPECTED_PARAMETER_SHA256 = (
    "7840923fb74e4a523e042f2c50410580cd7f2b1a34601c48fc328c9b5f42395b"
)
EXPECTED_TOKEN_ID_SHA256 = (
    "9c29dc292fe7e89cc22fafbeb953d48ff64821037378bec25189c8f185bf8359"
)
EXPECTED_PRETOKENIZER_SHA256 = (
    "9fb1975ab83e3fb658575a44de4af367dc46683d0a541a4f67dfb1ae4d414171"
)
EXPECTED_BASE_REVISION = "8ccc9b6f36199bec6961081d44eb72fb3f7353f3"

EXPECTED_FILES = {
    "SHA256SUMS.txt": (
        450,
        "aa78fce45c7fd1d382301a919a65a8f1b82ec4c18276c3491477291d98ebae23",
    ),
    "initialisation_manifest.json": (
        3629,
        "56db8a75903e7f8a903e55aec5f86e9800c21c9e40cdb130e6d0e2c40be22a03",
    ),
    "model/config.json": (
        1171,
        "7c3e21e3737140b8e9cc404cad5392d890becac306251a5f71362f96ccc5351c",
    ),
    "model/model.safetensors": (
        737722332,
        "4682e5e84b95ce49bbaa05bac090d1edf38ac9f71d68b5327313b304425a036c",
    ),
    "model/tokenizer.json": (
        8339093,
        "3bd1f6a24a2c99354b5f36e826e877d92d01a80dc24c3c5b74d31aaf87637e4e",
    ),
    "model/tokenizer_config.json": (
        508,
        "53f3b008c8696b8863912f9134436172f0ac6f15163c720fe1f976bcedbc5f8c",
    ),
}

EXPECTED_LABEL2ID = {
    "presumed_truthful": 0,
    "human_deceptive": 1,
    "ai_generated": 2,
}
EXPECTED_ID2LABEL = {
    "0": "presumed_truthful",
    "1": "human_deceptive",
    "2": "ai_generated",
}
EXPECTED_MISSING = {
    "classifier.bias",
    "classifier.weight",
    "pooler.dense.bias",
    "pooler.dense.weight",
}
EXPECTED_UNUSED = {
    "lm_predictions.lm_head.LayerNorm.bias",
    "lm_predictions.lm_head.LayerNorm.weight",
    "lm_predictions.lm_head.bias",
    "lm_predictions.lm_head.dense.bias",
    "lm_predictions.lm_head.dense.weight",
    "mask_predictions.LayerNorm.bias",
    "mask_predictions.LayerNorm.weight",
    "mask_predictions.classifier.bias",
    "mask_predictions.classifier.weight",
    "mask_predictions.dense.bias",
    "mask_predictions.dense.weight",
}


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


print("=" * WIDTH)
print("PHASE 2B — STEP M1C-C: RE-UPLOADED THREE-CLASS INITIALISATION VERIFICATION")
print("=" * WIDTH)
print("Python     :", sys.version.split()[0])
print("Input root :", INPUT_ROOT)
require(INPUT_ROOT.is_dir(), "Kaggle input root is unavailable")

section("UPSTREAM CONTINUITY")
t2_candidates = sorted(INPUT_ROOT.rglob("corpus_manifest.json"))
base_candidates = sorted(INPUT_ROOT.rglob("checkpoint_manifest.json"))
initialised_candidates = sorted(INPUT_ROOT.rglob("initialisation_manifest.json"))
require(len(t2_candidates) == 1, f"expected one T2 manifest; found {len(t2_candidates)}")
require(len(base_candidates) == 1, f"expected one base manifest; found {len(base_candidates)}")
require(
    len(initialised_candidates) == 1,
    f"expected one initialisation manifest; found {len(initialised_candidates)}",
)

t2_manifest = json.loads(t2_candidates[0].read_text(encoding="utf-8"))
base_manifest = json.loads(base_candidates[0].read_text(encoding="utf-8"))
require(t2_manifest.get("manifest_payload_sha256") == EXPECTED_T2_PAYLOAD, "T2 payload differs")
require(base_manifest.get("manifest_payload_sha256") == EXPECTED_BASE_PAYLOAD, "base payload differs")

ARTIFACT_ROOT = initialised_candidates[0].parent
print("T2 payload            :", EXPECTED_T2_PAYLOAD, "PASS")
print("Base payload          :", EXPECTED_BASE_PAYLOAD, "PASS")
print("Initialised root      :", ARTIFACT_ROOT)

section("EXTERNAL ZIP PROVENANCE")
sidecars = sorted(INPUT_ROOT.rglob("phase2B_DEBERTA_V3_3CLASS_INITIALISED.zip.sha256.txt"))
require(len(sidecars) == 1, f"expected one ZIP checksum sidecar; found {len(sidecars)}")
sidecar_tokens = sidecars[0].read_text(encoding="utf-8", errors="strict").strip().split()
require(sidecar_tokens, "ZIP checksum sidecar is empty")
require(sidecar_tokens[0].lower() == EXPECTED_ZIP_SHA256, "ZIP sidecar checksum differs")
print("Checksum sidecar      :", sidecars[0])
print("Recorded ZIP SHA256   :", sidecar_tokens[0].lower())

mounted_zips = sorted(INPUT_ROOT.rglob("phase2B_DEBERTA_V3_3CLASS_INITIALISED.zip"))
require(len(mounted_zips) <= 1, "multiple mounted initialisation ZIPs found")
if mounted_zips:
    require(file_sha256(mounted_zips[0]) == EXPECTED_ZIP_SHA256, "mounted ZIP checksum differs")
    print("ZIP runtime status    : BYTE_VERIFIED_IN_RUNTIME")
else:
    print("ZIP runtime status    : Kaggle-extracted; externally verified ZIP recorded")

section("COMPLETE ARTIFACT FILE REGISTRY")
actual_files = {
    path.relative_to(ARTIFACT_ROOT).as_posix()
    for path in ARTIFACT_ROOT.rglob("*")
    if path.is_file()
}
require(actual_files == set(EXPECTED_FILES), f"artifact file set differs: {sorted(actual_files)}")

for relative_name, (expected_size, expected_hash) in EXPECTED_FILES.items():
    path = ARTIFACT_ROOT / relative_name
    require(path.stat().st_size == expected_size, f"size mismatch: {relative_name}")
    require(file_sha256(path) == expected_hash, f"checksum mismatch: {relative_name}")
    print(f"{relative_name:48s} {expected_size:12d} bytes  PASS")

section("INTERNAL SHA-256 REGISTRY")
sums_path = ARTIFACT_ROOT / "SHA256SUMS.txt"
internal_registry = {}
for line_number, line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), start=1):
    parts = line.split(None, 1)
    require(len(parts) == 2, f"malformed SHA256SUMS line {line_number}")
    internal_registry[parts[1].strip()] = parts[0].lower()

expected_internal_registry = {
    name: details[1]
    for name, details in EXPECTED_FILES.items()
    if name != "SHA256SUMS.txt"
}
require(internal_registry == expected_internal_registry, "internal SHA256SUMS registry differs")
print("Registry entries       :", len(internal_registry))
print("Registry verification  : PASS")

section("INITIALISATION MANIFEST CONTRACT")
manifest = json.loads(initialised_candidates[0].read_text(encoding="utf-8"))
stored_payload = manifest.get("manifest_payload_sha256")
manifest_payload = {
    key: value for key, value in manifest.items()
    if key != "manifest_payload_sha256"
}
recomputed_payload = canonical_sha256(manifest_payload)
require(stored_payload == EXPECTED_INITIALISATION_PAYLOAD, "stored initialisation payload differs")
require(recomputed_payload == EXPECTED_INITIALISATION_PAYLOAD, "recomputed initialisation payload differs")
require(manifest_payload.get("phase") == "Phase 2B", "phase differs")
require(manifest_payload.get("step") == "M1C-B", "step differs")
require(
    manifest_payload.get("status") == "FROZEN_THREE_CLASS_INITIALISATION",
    "initialisation status differs",
)

upstream = manifest_payload["upstream"]
require(upstream["t2_manifest_payload_sha256"] == EXPECTED_T2_PAYLOAD, "manifest T2 link differs")
require(
    upstream["base_checkpoint_manifest_payload_sha256"] == EXPECTED_BASE_PAYLOAD,
    "manifest base link differs",
)
require(upstream["resolved_revision"] == EXPECTED_BASE_REVISION, "base revision differs")

initialisation = manifest_payload["initialisation"]
require(initialisation["seed"] == 42, "initialisation seed differs")
require(initialisation["num_labels"] == 3, "number of labels differs")
require(initialisation["label2id"] == EXPECTED_LABEL2ID, "label2id differs")
require(initialisation["id2label"] == EXPECTED_ID2LABEL, "id2label differs")
require(initialisation["model_class"] == "DebertaV2ForSequenceClassification", "model class differs")
require(initialisation["problem_type"] == "single_label_classification", "problem type differs")
require(set(initialisation["newly_initialised_keys"]) == EXPECTED_MISSING, "new parameter set differs")
require(set(initialisation["unused_pretraining_keys"]) == EXPECTED_UNUSED, "unused parameter set differs")
require(initialisation["mismatched_keys"] == [], "mismatched parameters recorded")
require(initialisation["parameter_count"] == 184424451, "parameter count differs")
require(initialisation["trainable_parameter_count"] == 184424451, "trainable parameter count differs")
require(initialisation["parameter_sha256"] == EXPECTED_PARAMETER_SHA256, "parameter SHA256 differs")
require(initialisation["tokenizer_class"] == "DebertaV2Tokenizer", "tokenizer class differs")
require(initialisation["tokenizer_is_fast"] is True, "tokenizer backend record differs")
require(initialisation["tokenizer_vocab_size"] == 128000, "tokenizer vocabulary size differs")
require(
    initialisation["tokenizer_policy"] == "native_deberta_unigram_metaspace_no_mistral_regex_patch",
    "tokenizer policy differs",
)
require(initialisation["eligible_texts_tokenised"] == 3186, "tokenized corpus count differs")
require(initialisation["pretokenizer_sha256"] == EXPECTED_PRETOKENIZER_SHA256, "pre-tokenizer hash differs")
require(
    initialisation["eligible_corpus_token_ids_sha256"] == EXPECTED_TOKEN_ID_SHA256,
    "token-ID fingerprint differs",
)
require(initialisation["tokenizer_save_reload_identity"] is True, "tokenizer reload identity not confirmed")
require(manifest_payload["training_performed"] is False, "manifest records training")
require(manifest_payload["inference_performed"] is False, "manifest records inference")

expected_model_registry = {
    name: {"size_bytes": details[0], "sha256": details[1]}
    for name, details in EXPECTED_FILES.items()
    if name.startswith("model/")
}
require(manifest_payload["artifact_files"] == expected_model_registry, "manifest artifact registry differs")

print("Stored payload         :", stored_payload)
print("Recomputed payload     :", recomputed_payload)
print("Parameter SHA256       :", initialisation["parameter_sha256"])
print("Pre-tokenizer SHA256   :", initialisation["pretokenizer_sha256"])
print("Token-ID SHA256        :", initialisation["eligible_corpus_token_ids_sha256"])
print("Label mapping          :", initialisation["label2id"])
print("Manifest verification  : PASS")

PHASE2B_INITIALISED_CHECKPOINT_ROOT = ARTIFACT_ROOT / "model"
PHASE2B_INITIALISED_CHECKPOINT = {
    "root": str(PHASE2B_INITIALISED_CHECKPOINT_ROOT),
    "zip_sha256": EXPECTED_ZIP_SHA256,
    "manifest_payload_sha256": EXPECTED_INITIALISATION_PAYLOAD,
    "parameter_sha256": EXPECTED_PARAMETER_SHA256,
    "token_id_sha256": EXPECTED_TOKEN_ID_SHA256,
}

print("\n" + "=" * WIDTH)
print("STEP M1C-C DECISION: PASS — RE-UPLOADED THREE-CLASS INITIALISATION VERIFIED")
print("=" * WIDTH)
print("Model loaded       : False")
print("Tokenizer loaded   : False")
print("Training/inference : NONE")
print("No file was written, extracted, transformed or modified.")
print("STOP — share this complete output before the model/hyperparameter contract is frozen.")
