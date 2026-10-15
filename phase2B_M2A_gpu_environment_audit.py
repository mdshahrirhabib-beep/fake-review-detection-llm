from pathlib import Path
from importlib.metadata import PackageNotFoundError, version
import hashlib
import json
import os
import platform
import subprocess
import sys


# This must be set before importing torch or creating a CUDA context.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch


WIDTH = 120
INPUT_ROOT = Path("/kaggle/input")
EXPECTED_T2_PAYLOAD = "b87c3945e0b50df788801c14cb9fcb2c88bf569e7c4556d9bfc168f8eb18cba8"
EXPECTED_BASE_PAYLOAD = "da21152ffc73c474d53485d3c0673eb0869cd50894d937acd1a2feb79eb8f33c"
EXPECTED_INITIALISATION_PAYLOAD = "171154b7225ded4b88d0024a5ba20e2314bee3213dc0d16c3575a40bec13fd45"
EXPECTED_INITIAL_MODEL_SHA256 = "4682e5e84b95ce49bbaa05bac090d1edf38ac9f71d68b5327313b304425a036c"
EXPECTED_INITIAL_MODEL_SIZE = 737722332
EXPECTED_INITIAL_PARAMETER_SHA256 = "7840923fb74e4a523e042f2c50410580cd7f2b1a34601c48fc328c9b5f42395b"
EXPECTED_TOKEN_ID_SHA256 = "9c29dc292fe7e89cc22fafbeb953d48ff64821037378bec25189c8f185bf8359"

EXPECTED_PACKAGES = {
    "numpy": "2.0.2",
    "pandas": "2.3.3",
    "scipy": "1.16.3",
    "scikit-learn": "1.6.1",
    "joblib": "1.5.3",
    "transformers": "5.0.0",
    "tokenizers": "0.22.2",
    "accelerate": "1.13.0",
    "safetensors": "0.7.0",
    "sentencepiece": "0.2.1",
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


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "MISSING"


print("=" * WIDTH)
print("PHASE 2B — STEP M2A: GPU TRAINING-ENVIRONMENT AND FROZEN-INPUT CONTINUITY AUDIT")
print("=" * WIDTH)
print("Python executable :", sys.executable)
print("Python version    :", sys.version.split()[0])
print("Platform          :", platform.platform())
print("Processor         :", platform.machine())

require(INPUT_ROOT.is_dir(), "Kaggle input root is unavailable")
require(os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "CUDA workspace setting differs")

section("FROZEN INPUT CONTINUITY")
t2_candidates = sorted(INPUT_ROOT.rglob("corpus_manifest.json"))
base_candidates = sorted(INPUT_ROOT.rglob("checkpoint_manifest.json"))
initialised_candidates = sorted(INPUT_ROOT.rglob("initialisation_manifest.json"))
require(len(t2_candidates) == 1, f"expected one T2 manifest; found {len(t2_candidates)}")
require(len(base_candidates) == 1, f"expected one base manifest; found {len(base_candidates)}")
require(len(initialised_candidates) == 1, f"expected one initialisation manifest; found {len(initialised_candidates)}")

t2_manifest = json.loads(t2_candidates[0].read_text(encoding="utf-8"))
base_manifest = json.loads(base_candidates[0].read_text(encoding="utf-8"))
initialised_manifest = json.loads(initialised_candidates[0].read_text(encoding="utf-8"))
require(t2_manifest.get("manifest_payload_sha256") == EXPECTED_T2_PAYLOAD, "T2 payload differs")
require(base_manifest.get("manifest_payload_sha256") == EXPECTED_BASE_PAYLOAD, "base payload differs")
require(
    initialised_manifest.get("manifest_payload_sha256") == EXPECTED_INITIALISATION_PAYLOAD,
    "initialisation payload differs",
)
initialisation = initialised_manifest["initialisation"]
require(initialisation["parameter_sha256"] == EXPECTED_INITIAL_PARAMETER_SHA256, "parameter identity differs")
require(initialisation["eligible_corpus_token_ids_sha256"] == EXPECTED_TOKEN_ID_SHA256, "token-ID identity differs")

INITIALISED_MODEL_ROOT = initialised_candidates[0].parent / "model"
model_path = INITIALISED_MODEL_ROOT / "model.safetensors"
require(model_path.is_file(), "initialised model.safetensors is missing")
require(model_path.stat().st_size == EXPECTED_INITIAL_MODEL_SIZE, "initialised model size differs")
require(file_sha256(model_path) == EXPECTED_INITIAL_MODEL_SHA256, "initialised model checksum differs")

print("T2 payload             :", EXPECTED_T2_PAYLOAD, "PASS")
print("Base payload           :", EXPECTED_BASE_PAYLOAD, "PASS")
print("Initialisation payload :", EXPECTED_INITIALISATION_PAYLOAD, "PASS")
print("Initial parameter      :", EXPECTED_INITIAL_PARAMETER_SHA256, "PASS")
print("Token-ID fingerprint   :", EXPECTED_TOKEN_ID_SHA256, "PASS")
print("Initialised model file :", EXPECTED_INITIAL_MODEL_SHA256, "PASS")

section("CRITICAL PACKAGE VERSIONS")
actual_packages = {name: package_version(name) for name in EXPECTED_PACKAGES}
for name, expected in EXPECTED_PACKAGES.items():
    actual = actual_packages[name]
    status = "PASS" if actual == expected else "STOP"
    print(f"{name:18s}: {actual:18s} expected {expected:10s} {status}")
    require(actual == expected, f"{name} version differs: {actual} != {expected}")

torch_public_version = torch.__version__.split("+")[0]
require(torch_public_version == "2.10.0", f"PyTorch base version differs: {torch.__version__}")
print(f"{'torch':18s}: {torch.__version__:18s} expected base 2.10.0 PASS")

section("CUDA AND GPU IDENTITY")
require(torch.cuda.is_available(), "CUDA is unavailable; switch the notebook accelerator to GPU")
device_count = torch.cuda.device_count()
require(device_count >= 1, "no CUDA device was detected")
require(torch.version.cuda is not None, "PyTorch has no CUDA build")

devices = []
for index in range(device_count):
    props = torch.cuda.get_device_properties(index)
    device = {
        "index": index,
        "name": props.name,
        "total_memory_bytes": int(props.total_memory),
        "compute_capability": list(torch.cuda.get_device_capability(index)),
        "multiprocessor_count": int(props.multi_processor_count),
    }
    devices.append(device)
    print(
        f"GPU {index}: {device['name']} | memory={device['total_memory_bytes']} bytes | "
        f"capability={device['compute_capability']} | MPs={device['multiprocessor_count']}"
    )

print("CUDA available          :", torch.cuda.is_available())
print("CUDA device count       :", device_count)
print("PyTorch CUDA build      :", torch.version.cuda)
print("cuDNN version           :", torch.backends.cudnn.version())
print("Selected training device: cuda:0")
print("Multi-GPU training      : prohibited; additional devices, if present, remain unused")
print("CUBLAS workspace        :", os.environ["CUBLAS_WORKSPACE_CONFIG"])

try:
    nvidia_smi = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip().splitlines()
except Exception as exc:
    nvidia_smi = [f"UNAVAILABLE: {type(exc).__name__}: {exc}"]

print("nvidia-smi identity:")
for line in nvidia_smi:
    print(" ", line)

environment_payload = {
    "phase": "Phase 2B",
    "step": "M2A",
    "status": "GPU_ENVIRONMENT_AUDITED",
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "processor": platform.machine(),
    "packages": {**actual_packages, "torch": torch.__version__},
    "cuda": {
        "available": True,
        "device_count": device_count,
        "pytorch_cuda_build": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "selected_device": "cuda:0",
        "multi_gpu_training": False,
        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
        "devices": devices,
        "nvidia_smi": nvidia_smi,
    },
    "frozen_inputs": {
        "t2_manifest_payload_sha256": EXPECTED_T2_PAYLOAD,
        "base_manifest_payload_sha256": EXPECTED_BASE_PAYLOAD,
        "initialisation_manifest_payload_sha256": EXPECTED_INITIALISATION_PAYLOAD,
        "initial_parameter_sha256": EXPECTED_INITIAL_PARAMETER_SHA256,
        "token_id_sha256": EXPECTED_TOKEN_ID_SHA256,
        "initialised_model_file_sha256": EXPECTED_INITIAL_MODEL_SHA256,
    },
}
environment_payload_sha256 = canonical_sha256(environment_payload)

print("\n" + "=" * WIDTH)
print("STEP M2A DECISION: PASS — GPU TRAINING ENVIRONMENT AND FROZEN INPUTS VERIFIED")
print("=" * WIDTH)
print("Environment payload SHA256:", environment_payload_sha256)
print("Model/tokenizer loaded     : False")
print("Training/inference       : NONE")
print("No file was written, transformed or modified.")
print("STOP — share this complete output before the M2 contract is frozen.")
