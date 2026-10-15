from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import html
import json
import re
import unicodedata
import zipfile

import pandas as pd


WIDTH = 110

OTT_ROOT = Path(
    "/kaggle/input/datasets/mdshahrirhabib/"
    "ott-op-spam-v14-raw/op_spam_v1.4"
)
OTT_CSV = Path(
    "/kaggle/input/datasets/rtatman/"
    "deceptive-opinion-spam-corpus/deceptive-opinion.csv"
)
AI_ROOT = Path("/kaggle/working/op_spam_AI")

EXTERNAL_OTT_ARCHIVE_SIZE = 1_172_634
EXTERNAL_OTT_ARCHIVE_SHA256 = (
    "e3a61b3709ccaca842aeec7f525e273988cf3b1bab35151712cf89759a6724fa"
)
EXPECTED_OTT_TREE_SHA256 = (
    "d9072b7a35bffa852e0d70f97aad3fff9f9fd67ee94bb7592a56f9b7a99a1661"
)
EXPECTED_OTT_CSV_SHA256 = (
    "e98f9f9497fb9e056b7f5870b2fd551e706dcca8de3fd8269f9f1f0de71e3a77"
)

AI_SPECS = [
    {
        "generator": "GPT3",
        "polarity": "negative",
        "filename": "generated_GPT3_negative.zip",
        "sha256": "c832882dc356cd1b4c7d28912ab882659ff2e1ff6b169652869ebf9ef25167de",
        "expected_prefix": "g",
    },
    {
        "generator": "GPT3",
        "polarity": "positive",
        "filename": "generated_GPT3_positive.zip",
        "sha256": "e66201d2b55568e4f078f556b473e35fc232b1eab7cda8e8ab41d1736345b244",
        "expected_prefix": "g",
    },
    {
        "generator": "Llama",
        "polarity": "negative",
        "filename": "generated_LLama_negative.zip",
        "sha256": "aabb852f6958443e9ca88978355acc26cfab78e920a1948486f5f863567810cf",
        "expected_prefix": "t",
    },
    {
        "generator": "Llama",
        "polarity": "positive",
        "filename": "generated_LLama_positive.zip",
        "sha256": "386f7e1c53d9ef34f47164200de63d5cc9295d0d70e28d1d787c1474de35e37e",
        "expected_prefix": "t",
    },
]


def require(condition, message):
    if not condition:
        raise RuntimeError("STOP — " + message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_decode(data, source_name):
    """Decode without silently replacing any byte."""
    if data.startswith(b"\xef\xbb\xbf"):
        try:
            return data.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError:
            pass
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            return data.decode("cp1252"), "cp1252"
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                f"STOP — strict decoding failed for {source_name}"
            ) from exc


def basic_normalise(value):
    value = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", value).strip()


def casefold_normalise(value):
    return basic_normalise(value).casefold()


def html_normalise(value):
    return casefold_normalise(html.unescape(str(value)))


def lexical_normalise(value):
    """Audit-only ordered word-token representation; not model input."""
    value = html.unescape(str(value))
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"\w+", value, flags=re.UNICODE))


def first_ten_words(value):
    return tuple(basic_normalise(value).split()[:10])


def relaxed_first_ten(value):
    value = html.unescape(str(value))
    value = unicodedata.normalize("NFKC", value).casefold()
    return tuple(re.findall(r"\w+", value, flags=re.UNICODE)[:10])


def section(title):
    print(f"\n{title}")
    print("-" * WIDTH)


print("=" * WIDTH)
print("PHASE 2B — GATE T0R: FINAL RAW-OTT AND AI SEED-FAMILY VERIFICATION")
print("=" * WIDTH)

require(OTT_ROOT.is_dir(), f"raw Ott directory missing: {OTT_ROOT}")
require(OTT_CSV.is_file(), f"Ott Kaggle CSV missing: {OTT_CSV}")
require(AI_ROOT.is_dir(), f"op_spam_AI repository missing: {AI_ROOT}")

section("SOURCE PROVENANCE")
print("Official Ott extracted root :", OTT_ROOT)
print("External archive size       :", EXTERNAL_OTT_ARCHIVE_SIZE)
print("External archive SHA256     :", EXTERNAL_OTT_ARCHIVE_SHA256)
print("Archive verification        : Windows PC using CertUtil")
print("Kaggle representation       : automatically extracted directory")
print("Kaggle corroborating CSV    :", OTT_CSV)
print("op_spam_AI repository       :", AI_ROOT)


# Deterministic identity for the Kaggle-extracted official archive.
all_ott_files = sorted(path for path in OTT_ROOT.rglob("*") if path.is_file())
tree_entries = []
for path in all_ott_files:
    raw_bytes = path.read_bytes()
    tree_entries.append(
        {
            "relative_path": path.relative_to(OTT_ROOT).as_posix(),
            "size_bytes": len(raw_bytes),
            "sha256": sha256_bytes(raw_bytes),
        }
    )
tree_payload = json.dumps(
    tree_entries,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
tree_sha256 = sha256_bytes(tree_payload)

section("EXTRACTED TREE IDENTITY")
print("Total extracted files :", len(all_ott_files))
print("Tree-manifest SHA256  :", tree_sha256)
require(len(all_ott_files) == 1602, "expected 1,602 extracted files")
require(
    tree_sha256 == EXPECTED_OTT_TREE_SHA256,
    "extracted Ott tree SHA-256 differs from the verified tree",
)


# Parse the 1,600 official raw review files.
review_files = sorted(OTT_ROOT.rglob("*.txt"))
require(len(review_files) == 1600, "expected exactly 1,600 Ott review files")

filename_pattern = re.compile(r"^([dgt])_(.+)_(\d+)\.txt$")
source_mapping = {
    "deceptive_from_MTurk": ("deceptive", "MTurk"),
    "truthful_from_TripAdvisor": ("truthful", "TripAdvisor"),
    "truthful_from_Web": ("truthful", "Web"),
}

ott_rows = []
ott_keys = set()
ott_encoding_counts = Counter()

for path in review_files:
    relative = path.relative_to(OTT_ROOT)
    require(len(relative.parts) == 4, f"unexpected Ott path: {relative}")
    polarity_dir, source_dir, fold_dir, filename = relative.parts
    require(
        polarity_dir in {"positive_polarity", "negative_polarity"},
        f"unknown polarity directory: {relative}",
    )
    require(source_dir in source_mapping, f"unknown source: {relative}")
    require(re.fullmatch(r"fold[1-5]", fold_dir), f"invalid fold: {relative}")
    match = filename_pattern.fullmatch(filename)
    require(match is not None, f"invalid Ott filename: {relative}")
    prefix, hotel, review_index_text = match.groups()
    review_class, source = source_mapping[source_dir]
    expected_prefix = "d" if review_class == "deceptive" else "t"
    require(prefix == expected_prefix, f"class-prefix conflict: {relative}")
    polarity = polarity_dir.replace("_polarity", "")
    fold = int(fold_dir.replace("fold", ""))
    review_index = int(review_index_text)
    require(1 <= review_index <= 20, f"index outside 1–20: {relative}")
    raw_bytes = path.read_bytes()
    text, encoding = strict_decode(raw_bytes, str(relative))
    ott_encoding_counts[encoding] += 1
    key = (review_class, polarity, hotel, review_index)
    require(key not in ott_keys, f"duplicate Ott filename identity: {key}")
    ott_keys.add(key)
    ott_rows.append(
        {
            "review_class": review_class,
            "polarity": polarity,
            "source": source,
            "fold": fold,
            "hotel": hotel,
            "review_index": review_index,
            "text": basic_normalise(text),
            "file_sha256": sha256_bytes(raw_bytes),
            "relative_path": relative.as_posix(),
        }
    )

ott_class_counts = Counter(row["review_class"] for row in ott_rows)
ott_polarity_counts = Counter(row["polarity"] for row in ott_rows)
ott_source_counts = Counter(row["source"] for row in ott_rows)
ott_fold_counts = Counter(row["fold"] for row in ott_rows)
ott_cell_counts = Counter(
    (row["review_class"], row["polarity"], row["hotel"])
    for row in ott_rows
)

require(ott_class_counts == {"truthful": 800, "deceptive": 800}, "class counts differ")
require(ott_polarity_counts == {"positive": 800, "negative": 800}, "polarity counts differ")
require(
    ott_source_counts == {"MTurk": 800, "TripAdvisor": 400, "Web": 400},
    "source counts differ",
)
require(ott_fold_counts == {1: 320, 2: 320, 3: 320, 4: 320, 5: 320}, "fold counts differ")
require(len(ott_cell_counts) == 80, "expected 80 class × polarity × hotel cells")
require(set(ott_cell_counts.values()) == {20}, "Ott cells are not balanced at 20")

section("RAW OTT STRUCTURE")
print("Review files     :", len(ott_rows))
print("Class counts     :", dict(ott_class_counts))
print("Polarity counts  :", dict(ott_polarity_counts))
print("Source counts    :", dict(ott_source_counts))
print("Fold counts      :", dict(sorted(ott_fold_counts.items())))
print("Encoding counts  :", dict(ott_encoding_counts))
print("Balanced cells   :", len(ott_cell_counts), "cells × 20 reviews")


# Diagnose the raw-source / derived-CSV representation difference.
actual_csv_sha256 = file_sha256(OTT_CSV)
require(actual_csv_sha256 == EXPECTED_OTT_CSV_SHA256, "Ott CSV SHA-256 changed")
csv_frame = pd.read_csv(OTT_CSV)
required_columns = {"deceptive", "hotel", "polarity", "source", "text"}
require(required_columns.issubset(csv_frame.columns), "Ott CSV schema mismatch")
require(len(csv_frame) == 1600, "Ott CSV must contain 1,600 rows")


def raw_metadata(row):
    return (
        row["review_class"].strip().casefold(),
        row["hotel"].strip().casefold(),
        row["polarity"].strip().casefold(),
        row["source"].strip().casefold(),
    )


def csv_metadata(row):
    return (
        str(row.deceptive).strip().casefold(),
        str(row.hotel).strip().casefold(),
        str(row.polarity).strip().casefold(),
        str(row.source).strip().casefold(),
    )


raw_metadata_multiset = Counter(raw_metadata(row) for row in ott_rows)
csv_metadata_multiset = Counter(
    csv_metadata(row) for row in csv_frame.itertuples(index=False)
)
require(
    raw_metadata_multiset == csv_metadata_multiset,
    "raw Ott and CSV metadata distributions differ",
)


def raw_comparison_counter(normaliser):
    return Counter(
        raw_metadata(row) + (normaliser(row["text"]),)
        for row in ott_rows
    )


def csv_comparison_counter(normaliser):
    return Counter(
        csv_metadata(row) + (normaliser(row.text),)
        for row in csv_frame.itertuples(index=False)
    )


comparison_definitions = [
    ("NFKC + whitespace", basic_normalise),
    ("plus casefold", casefold_normalise),
    ("plus HTML unescape", html_normalise),
    ("ordered word tokens", lexical_normalise),
]
comparison_results = []
for comparison_name, normaliser in comparison_definitions:
    raw_counter = raw_comparison_counter(normaliser)
    csv_counter = csv_comparison_counter(normaliser)
    matched = sum((raw_counter & csv_counter).values())
    comparison_results.append(
        {
            "comparison": comparison_name,
            "matched": matched,
            "raw_unmatched": len(ott_rows) - matched,
            "csv_unmatched": len(csv_frame) - matched,
            "identical": raw_counter == csv_counter,
        }
    )

observed_matches = {
    result["comparison"]: result["matched"] for result in comparison_results
}
require(observed_matches["NFKC + whitespace"] == 1295, "strict match count changed")
require(observed_matches["plus casefold"] == 1295, "casefold match count changed")
require(observed_matches["plus HTML unescape"] == 1295, "HTML match count changed")
require(observed_matches["ordered word tokens"] == 1600, "lexical match count changed")
require(comparison_results[-1]["identical"], "lexical multisets differ")

strict_match_n = observed_matches["NFKC + whitespace"]
representation_difference_n = 1600 - strict_match_n
lexical_match_n = observed_matches["ordered word tokens"]

section("RAW-OTT / KAGGLE-CSV DIAGNOSTIC")
print(pd.DataFrame(comparison_results).to_string(index=False))
print("\nDIAGNOSTIC DETERMINATION")
print("-" * WIDTH)
print("Kaggle CSV SHA256                 :", actual_csv_sha256)
print("Metadata distributions            : IDENTICAL")
print("Strict text matches               :", strict_match_n)
print("Non-lexical representation diffs  :", representation_difference_n)
print("Ordered word-token matches        :", lexical_match_n)
print("Lexical multiset identical        :", True)
print("Authoritative modelling text      : official raw Ott files")
print("Kaggle CSV role                   : corroborating derived representation")
print("Sources merged                    :", False)
print(
    "Interpretation: 305 records differ in punctuation-level representation "
    "while preserving the complete ordered word-token multiset within each "
    "metadata cell."
)


# Build the authoritative truthful-parent index from raw filenames.
parent_lookup = {}
for row in ott_rows:
    if row["review_class"] != "truthful":
        continue
    parent_key = (row["polarity"], row["hotel"], row["review_index"])
    require(parent_key not in parent_lookup, f"non-unique parent: {parent_key}")
    parent_lookup[parent_key] = row
require(len(parent_lookup) == 800, "expected 800 truthful parents")

section("AUTHORITATIVE TRUTHFUL-PARENT INDEX")
print("Truthful parent files :", len(parent_lookup))
print("Parent identity key   : polarity + hotel + numerical filename index")
print("Parent source         : official raw Ott files")


# Parse the four AI archives and resolve every review to its raw truthful parent.
ai_rows = []
ai_keys = set()
ai_encoding_counts = Counter()
ai_archive_results = []

for specification in AI_SPECS:
    generator = specification["generator"]
    polarity = specification["polarity"]
    zip_name = specification["filename"]
    expected_hash = specification["sha256"]
    expected_prefix = specification["expected_prefix"]
    zip_path = AI_ROOT / zip_name
    require(zip_path.is_file(), f"AI archive missing: {zip_path}")
    actual_hash = file_sha256(zip_path)
    require(actual_hash == expected_hash, f"checksum mismatch: {zip_name}")
    valid_records = []
    excluded_metadata_members = 0
    ignored_non_text_members = 0

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member.is_dir():
                continue
            if "__MACOSX" in member_path.parts or member_path.name.startswith("._"):
                excluded_metadata_members += 1
                continue
            if member_path.suffix.lower() != ".txt":
                ignored_non_text_members += 1
                continue
            match = filename_pattern.fullmatch(member_path.name)
            require(match is not None, f"invalid AI filename: {member.filename}")
            prefix, hotel, review_index_text = match.groups()
            require(prefix == expected_prefix, f"unexpected prefix: {member.filename}")
            review_index = int(review_index_text)
            require(1 <= review_index <= 20, f"AI index outside 1–20: {member.filename}")
            ai_key = (generator, polarity, hotel, review_index)
            require(ai_key not in ai_keys, f"duplicate AI filename identity: {ai_key}")
            ai_keys.add(ai_key)
            parent_key = (polarity, hotel, review_index)
            require(parent_key in parent_lookup, f"truthful parent missing: {ai_key}")
            parent = parent_lookup[parent_key]
            raw_bytes = archive.read(member)
            ai_text, encoding = strict_decode(raw_bytes, f"{zip_name}:{member.filename}")
            ai_encoding_counts[encoding] += 1
            ai_text = basic_normalise(ai_text)
            record = {
                "generator": generator,
                "polarity": polarity,
                "hotel": hotel,
                "review_index": review_index,
                "fold": parent["fold"],
                "member_name": member.filename,
                "text": ai_text,
                "text_sha256": sha256_bytes(raw_bytes),
                "parent_path": parent["relative_path"],
                "parent_sha256": parent["file_sha256"],
                "exact_first_10_match": first_ten_words(ai_text)
                == first_ten_words(parent["text"]),
                "relaxed_first_10_match": relaxed_first_ten(ai_text)
                == relaxed_first_ten(parent["text"]),
            }
            valid_records.append(record)
            ai_rows.append(record)

    require(len(valid_records) == 400, f"{zip_name}: expected 400 reviews")
    hotel_counts = Counter(record["hotel"] for record in valid_records)
    require(len(hotel_counts) == 20, f"{zip_name}: expected 20 hotels")
    require(set(hotel_counts.values()) == {20}, f"{zip_name}: hotel imbalance")
    ai_archive_results.append(
        {
            "generator": generator,
            "polarity": polarity,
            "valid_reviews": len(valid_records),
            "hotels": len(hotel_counts),
            "reviews_per_hotel": 20,
            "metadata_members_excluded": excluded_metadata_members,
            "non_text_members_ignored": ignored_non_text_members,
        }
    )

require(len(ai_rows) == 1600, "expected exactly 1,600 AI reviews")
require(len(ai_keys) == 1600, "AI filename identities are not unique")

section("AI ARCHIVE VERIFICATION")
print(pd.DataFrame(ai_archive_results).to_string(index=False))
print("\nAI encoding counts :", dict(ai_encoding_counts))


# Report exact and punctuation-relaxed ten-word seed-prefix matches.
seed_summary = []
for generator in ["GPT3", "Llama"]:
    for polarity in ["negative", "positive"]:
        subset = [
            row
            for row in ai_rows
            if row["generator"] == generator and row["polarity"] == polarity
        ]
        hotel_counts = Counter(row["hotel"] for row in subset)
        exact_matches = sum(int(row["exact_first_10_match"]) for row in subset)
        relaxed_matches = sum(int(row["relaxed_first_10_match"]) for row in subset)
        require(len(subset) == 400, f"{generator}/{polarity}: count mismatch")
        require(len(hotel_counts) == 20, f"{generator}/{polarity}: hotel mismatch")
        require(set(hotel_counts.values()) == {20}, f"{generator}/{polarity}: imbalance")
        seed_summary.append(
            {
                "generator": generator,
                "polarity": polarity,
                "reviews": len(subset),
                "parents_resolved": len(subset),
                "exact_first_10": exact_matches,
                "relaxed_first_10": relaxed_matches,
                "prefix_differs": len(subset) - exact_matches,
                "unique_normalised_texts": len({row["text"] for row in subset}),
            }
        )

seed_summary_frame = pd.DataFrame(seed_summary)
total_exact_prefix_matches = int(seed_summary_frame["exact_first_10"].sum())
total_relaxed_prefix_matches = int(seed_summary_frame["relaxed_first_10"].sum())
total_prefix_differences = len(ai_rows) - total_exact_prefix_matches

section("AI SEED-FAMILY RESOLUTION")
print(seed_summary_frame.to_string(index=False))
print("\nGLOBAL SEED-FAMILY RESULTS")
print("-" * WIDTH)
print("AI reviews loaded             :", len(ai_rows))
print("Resolved by filename identity :", len(ai_rows))
print("Unresolved                    :", 0)
print("Exact first-ten-word matches  :", total_exact_prefix_matches)
print("Exact prefixes differing      :", total_prefix_differences)
print("Relaxed first-ten matches     :", total_relaxed_prefix_matches)
require(
    sum(row["parents_resolved"] for row in seed_summary) == 1600,
    "not all AI reviews received a truthful parent",
)


# Verify that each hotel belongs to one and only one official Ott fold.
hotel_folds = defaultdict(set)
for row in ott_rows:
    hotel_folds[row["hotel"]].add(row["fold"])
require(len(hotel_folds) == 20, "expected exactly 20 hotels")
require(all(len(folds) == 1 for folds in hotel_folds.values()), "hotel crosses folds")

fold_hotels = defaultdict(list)
for hotel, folds in hotel_folds.items():
    fold_hotels[next(iter(folds))].append(hotel)
require(set(fold_hotels) == {1, 2, 3, 4, 5}, "fold set mismatch")
require(all(len(hotels) == 4 for hotels in fold_hotels.values()), "fold hotel count mismatch")

for ai_row in ai_rows:
    expected_fold = next(iter(hotel_folds[ai_row["hotel"]]))
    require(ai_row["fold"] == expected_fold, "AI review inherited incorrect fold")

section("HOTEL-TO-FOLD MAPPING")
for fold in sorted(fold_hotels):
    print(f"Fold {fold}: " + ", ".join(sorted(fold_hotels[fold])))


# Record the known acquisition-source confounding.
truthful_source_by_polarity = Counter(
    (row["polarity"], row["source"])
    for row in ott_rows
    if row["review_class"] == "truthful"
)
deceptive_source_by_polarity = Counter(
    (row["polarity"], row["source"])
    for row in ott_rows
    if row["review_class"] == "deceptive"
)

section("SOURCE × POLARITY CONFOUNDING RECORD")
print("Truthful source × polarity :", dict(truthful_source_by_polarity))
print("Deceptive source × polarity:", dict(deceptive_source_by_polarity))
print(
    "Required limitation        : collection source is confounded with "
    "polarity in the truthful class."
)


# Freeze a deterministic result payload in console output. No file is written.
verification_payload = {
    "phase": "Phase 2B",
    "gate": "T0R",
    "status": "GO",
    "official_ott_archive": {
        "external_size_bytes": EXTERNAL_OTT_ARCHIVE_SIZE,
        "external_sha256": EXTERNAL_OTT_ARCHIVE_SHA256,
        "verification_location": "Windows PC CertUtil",
        "kaggle_representation": "automatically extracted",
        "extracted_tree_sha256": tree_sha256,
        "extracted_files": len(all_ott_files),
        "review_files": len(review_files),
    },
    "kaggle_csv": {
        "sha256": actual_csv_sha256,
        "role": "corroborating derived representation",
        "strict_matches": strict_match_n,
        "non_lexical_representation_differences": representation_difference_n,
        "ordered_word_token_matches": lexical_match_n,
        "metadata_multiset_identical": True,
        "lexical_multiset_identical": True,
    },
    "source_authority": {
        "modelling_text": "official raw Ott files",
        "filenames_and_folds": "official raw Ott files",
        "sources_merged": False,
    },
    "ott_counts": {
        "rows": len(ott_rows),
        "truthful": ott_class_counts["truthful"],
        "deceptive": ott_class_counts["deceptive"],
        "positive": ott_polarity_counts["positive"],
        "negative": ott_polarity_counts["negative"],
        "hotels": len(hotel_folds),
        "folds": len(fold_hotels),
    },
    "ai_counts": {
        "rows": len(ai_rows),
        "parents_resolved": len(ai_rows),
        "unresolved": 0,
        "exact_first_ten_matches": total_exact_prefix_matches,
        "exact_prefix_differences": total_prefix_differences,
        "relaxed_first_ten_matches": total_relaxed_prefix_matches,
    },
    "fold_hotels": {
        str(fold): sorted(hotels)
        for fold, hotels in sorted(fold_hotels.items())
    },
    "seed_summary": seed_summary,
    "source_confounding": {
        "truthful_positive": "TripAdvisor",
        "truthful_negative": "Web",
        "deceptive_positive_and_negative": "MTurk",
    },
    "prohibited_actions_completed": {
        "files_written": False,
        "rows_removed": False,
        "corpus_constructed": False,
        "split_created": False,
        "model_trained": False,
    },
}

verification_payload_bytes = json.dumps(
    verification_payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
verification_payload_sha256 = sha256_bytes(verification_payload_bytes)

print("\n" + "=" * WIDTH)
print("GATE T0R — GO")
print("=" * WIDTH)
print("✓ External Ott archive checksum recorded")
print("✓ Extracted Ott tree verified and frozen")
print("✓ All 1,600 Ott files decoded without replacement")
print("✓ Raw Ott structure, metadata and folds verified")
print("✓ Kaggle CSV is lexically equivalent within metadata cells")
print("✓ Official raw Ott files retained as authoritative modelling text")
print("✓ All 1,600 AI reviews resolved by filename identity")
print("✓ All 20 hotels remain confined to one official fold")
print("Verification payload SHA256:", verification_payload_sha256)
print("\nNo files written.")
print("No rows removed or modified.")
print("No corpus constructed.")
print("No split created.")
print("No model trained or evaluated.")
print("STOP — preserve and share this complete output before Gate T1.")
