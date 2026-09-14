"""Evaluate landmark recognition and out-of-domain rejection on local images."""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import mimetypes
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))

from core.config import settings  # noqa: E402
from core.database import engine  # noqa: E402
from evaluation.metrics import classification_metrics, latency_summary  # noqa: E402
from services.vision.image_recognition import recognize_image  # noqa: E402

DEFAULT_MANIFEST = PROJECT_ROOT / "evaluation" / "data" / "vision_manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "vision_results.json"
EXPECTED_REJECTION_CODES = {
    "UNRECOGNIZED",
    "NOT_AN_ARTIFACT",
    "LOW_CONFIDENCE",
    "INVALID_IMAGE",
}


def _git_commit() -> str:
    try:
        return subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={PROJECT_ROOT}",
                "rev-parse",
                "HEAD",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _to_data_url(path: Path) -> tuple[str, str]:
    content = path.read_bytes()
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime_type};base64,{encoded}", hashlib.sha256(content).hexdigest()


def _candidate_ids(result: Any) -> list[int]:
    candidates = list(getattr(result, "top_candidates", []) or [])
    candidates.sort(
        key=lambda item: float(item.get("final_score", item.get("confidence", 0.0)) or 0.0),
        reverse=True,
    )
    ids: list[int] = []
    for item in candidates:
        raw_id = item.get("artifact_id")
        if raw_id is None or not str(raw_id).isdigit():
            continue
        artifact_id = int(raw_id)
        if artifact_id not in ids:
            ids.append(artifact_id)
    recognized_id = getattr(result, "artifact_id", None)
    if recognized_id is not None and str(recognized_id).isdigit():
        recognized_int = int(recognized_id)
        if recognized_int in ids:
            ids.remove(recognized_int)
        ids.insert(0, recognized_int)
    return ids


def _is_provider_failure(row: dict[str, Any]) -> bool:
    return bool(row.get("error")) and row["error"] not in EXPECTED_REJECTION_CODES


def _build_result_payload(
    rows: list[dict[str, Any]],
    manifest_path: Path,
    skipped_duplicates: list[dict[str, str]],
    deduplicate: bool,
    manifest_images: int,
    complete: bool,
) -> dict[str, Any]:
    in_domain = [row for row in rows if row["expected_artifact_id"] is not None]
    ood = [row for row in rows if row["expected_artifact_id"] is None]
    valid_rows = [row for row in rows if not _is_provider_failure(row)]
    valid_in_domain = [
        row for row in valid_rows if row["expected_artifact_id"] is not None
    ]
    top1_correct = sum(
        row["predicted_artifact_id"] == row["expected_artifact_id"]
        for row in in_domain
    )
    top3_correct = sum(
        row["expected_artifact_id"] in row["candidate_artifact_ids"][:3]
        for row in in_domain
    )
    valid_top1_correct = sum(
        row["predicted_artifact_id"] == row["expected_artifact_id"]
        for row in valid_in_domain
    )
    expected_positive = [row["expected_artifact_id"] is not None for row in rows]
    predicted_positive = [
        row["recognized"] and row["predicted_artifact_id"] is not None
        for row in rows
    ]

    by_artifact: dict[str, dict[str, int | float]] = {}
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in in_domain:
        grouped[int(row["expected_artifact_id"])].append(row)
    for artifact_id, artifact_rows in sorted(grouped.items()):
        correct = sum(
            row["predicted_artifact_id"] == artifact_id for row in artifact_rows
        )
        by_artifact[str(artifact_id)] = {
            "count": len(artifact_rows),
            "top_1_accuracy": round(correct / len(artifact_rows), 4),
        }

    failures = sum(_is_provider_failure(row) for row in rows)
    return {
        "metadata": {
            "git_commit": _git_commit(),
            "manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
            "manifest_images": manifest_images,
            "vision_model": settings.GEMINI_VISION_MODEL,
            "configured_confidence_threshold": settings.VISION_CONFIDENCE_THRESHOLD,
            "deduplicated": deduplicate,
            "complete": complete,
        },
        "summary": {
            "evaluated_images": len(rows),
            "successful_inferences": len(valid_rows),
            "in_domain_images": len(in_domain),
            "ood_images": len(ood),
            "top_1_accuracy": round(top1_correct / len(in_domain), 4)
            if in_domain
            else 0.0,
            "top_3_recall": round(top3_correct / len(in_domain), 4)
            if in_domain
            else 0.0,
            "conditional_top_1_accuracy": round(
                valid_top1_correct / len(valid_in_domain), 4
            )
            if valid_in_domain
            else 0.0,
            "recognition_classification": classification_metrics(
                expected_positive, predicted_positive
            ),
            "ood_rejection_rate": round(
                sum(
                    not (
                        row["recognized"]
                        and row["predicted_artifact_id"] is not None
                    )
                    for row in ood
                )
                / len(ood),
                4,
            )
            if ood
            else 0.0,
            "provider_failures": failures,
            "provider_failure_rate": round(failures / len(rows), 4) if rows else 0.0,
            "latency": latency_summary(row["latency_ms"] for row in rows),
            "by_artifact": by_artifact,
        },
        "skipped_duplicates": skipped_duplicates,
        "cases": rows,
    }


def _write_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_path.replace(output_path)


async def run(
    manifest_path: Path,
    output_path: Path,
    delay_seconds: float,
    limit: int | None,
    deduplicate: bool,
    resume: bool,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if limit is not None:
        manifest = manifest[:limit]

    rows: list[dict[str, Any]] = []
    skipped_duplicates: list[dict[str, str]] = []
    seen_hashes: dict[str, str] = {}
    reusable_rows: dict[str, dict[str, Any]] = {}
    if resume and output_path.exists():
        cached_payload = json.loads(output_path.read_text(encoding="utf-8"))
        cached_metadata = cached_payload.get("metadata", {})
        if cached_metadata.get("vision_model") != settings.GEMINI_VISION_MODEL:
            raise ValueError(
                "Cannot resume Vision evaluation with a different model: "
                f"cached={cached_metadata.get('vision_model')}, "
                f"configured={settings.GEMINI_VISION_MODEL}"
            )
        reusable_rows = {
            row["path"]: row
            for row in cached_payload.get("cases", [])
            if not _is_provider_failure(row)
        }

    for index, item in enumerate(manifest, start=1):
        relative_path = Path(item["path"])
        image_path = PROJECT_ROOT / relative_path
        if not image_path.is_file():
            raise FileNotFoundError(f"Missing evaluation image: {relative_path}")

        data_url, sha256 = _to_data_url(image_path)
        if deduplicate and sha256 in seen_hashes:
            skipped_duplicates.append(
                {"path": relative_path.as_posix(), "duplicate_of": seen_hashes[sha256]}
            )
            continue
        seen_hashes[sha256] = relative_path.as_posix()

        expected_id = item.get("expected_artifact_id")
        expected_id = int(expected_id) if expected_id is not None else None
        cached_row = reusable_rows.get(relative_path.as_posix())
        if (
            cached_row
            and cached_row.get("sha256") == sha256
            and cached_row.get("expected_artifact_id") == expected_id
        ):
            rows.append(cached_row)
            print(
                f"vision: {index}/{len(manifest)} {relative_path.as_posix()} (reused)",
                flush=True,
            )
            continue

        started = time.perf_counter()
        result = await recognize_image(data_url, lang="vi")
        latency_ms = (time.perf_counter() - started) * 1000
        candidate_ids = _candidate_ids(result)
        predicted_id = (
            int(result.artifact_id)
            if result.artifact_id is not None and str(result.artifact_id).isdigit()
            else None
        )
        row = {
                "path": relative_path.as_posix(),
                "sha256": sha256,
                "expected_artifact_id": expected_id,
                "predicted_artifact_id": predicted_id,
                "recognized": bool(result.recognized),
                "raw_label": result.raw_label,
                "confidence_score": result.confidence_score,
                "final_score": getattr(result, "final_score", None),
                "candidate_artifact_ids": candidate_ids,
                "error": getattr(result, "error", None),
                "latency_ms": round(latency_ms, 3),
            }
        rows.append(row)
        _write_payload(
            output_path,
            _build_result_payload(
                rows,
                manifest_path,
                skipped_duplicates,
                deduplicate,
                len(manifest),
                complete=False,
            ),
        )
        print(
            f"vision: {index}/{len(manifest)} {relative_path.as_posix()}",
            flush=True,
        )
        if delay_seconds > 0 and index < len(manifest):
            await asyncio.sleep(delay_seconds)

    result_payload = _build_result_payload(
        rows,
        manifest_path,
        skipped_duplicates,
        deduplicate,
        len(manifest),
        complete=True,
    )
    _write_payload(output_path, result_payload)
    return result_payload


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--keep-duplicates", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse valid rows from the output file and retry provider failures only.",
    )
    args = parser.parse_args()

    try:
        result = await run(
            args.manifest.resolve(),
            args.output.resolve(),
            max(args.delay, 0.0),
            args.limit,
            not args.keep_duplicates,
            args.resume,
        )
        print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
