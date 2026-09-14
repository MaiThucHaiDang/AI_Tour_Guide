"""Generate a concise Markdown evaluation report from benchmark JSON artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
DEFAULT_OUTPUT = RESULTS_DIR / "evaluation_report.md"


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: Any) -> str:
    return f"{float(value) * 100:.1f}%"


def _number(value: Any, digits: int = 2) -> str:
    return "n/a" if value is None else f"{float(value):.{digits}f}"


def _percentage_points(value: Any) -> str:
    return f"{float(value) * 100:+.1f} pp"


def _ood_metrics(threshold: dict[str, Any]) -> dict[str, Any]:
    if "test_ood_detection" in threshold:
        return threshold["test_ood_detection"]

    # Backward compatibility for result files created before the positive class
    # was explicitly changed from in-domain to out-of-domain.
    original = threshold["test_classification"]
    tp = int(original["true_negative"])
    tn = int(original["true_positive"])
    fp = int(original["false_negative"])
    fn = int(original["false_positive"])
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "f1": round(f1, 4),
        "recall": round(recall, 4),
        "accuracy": original["accuracy"],
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
    }


def _rag_section(rag: dict[str, Any]) -> list[str]:
    metadata = rag["metadata"]
    entity = rag["entity_lookup"]["test"]
    retrieval = rag["vector_retrieval"]
    test = retrieval["test"]
    overall = test["overall"]
    latency = test["latency"]
    threshold = retrieval["ood_threshold"]
    selected = threshold["selected_on_dev"]
    ood_test = _ood_metrics(threshold)
    accepted_top1 = threshold["test_positive_correct_and_accepted_rate"]
    graph_mean = retrieval.get("test_graph_context_mean_artifacts")
    positive_test_rows = [
        row
        for row in rag.get("cases", {}).get("vector_positive", [])
        if row.get("split") == "test"
    ]
    ood_test_rows = [
        row
        for row in rag.get("cases", {}).get("vector_ood", [])
        if row.get("split") == "test"
    ]
    if graph_mean is None:
        graph_rows = [
            row
            for row in rag.get("cases", {}).get("vector_positive", [])
            if row.get("split") == "test"
        ]
        graph_mean = (
            sum(len(row.get("graph_context_artifact_ids", [])) for row in graph_rows)
            / len(graph_rows)
            if graph_rows
            else None
        )

    return [
        "## RAG and entity retrieval",
        "",
        f"- Dataset: {metadata['positive_queries']} labeled Vietnamese/English queries "
        f"and {metadata['ood_queries']} out-of-domain queries across the development/test splits.",
        f"- Index: {metadata['indexed_documents']} pgvector documents across "
        f"{metadata.get('indexed_artifacts', 'n/a')} landmarks using "
        f"`{metadata['embedding_model']}` embeddings.",
        f"- Knowledge graph: {metadata.get('knowledge_facts', 'n/a')} facts and "
        f"{metadata.get('graph_relations', 'n/a')} relations.",
        "",
        "| Metric | Held-out test result |",
        "|---|---:|",
        f"| Fuzzy entity-lookup accuracy (n={entity['count']}) | {_pct(entity['accuracy'])} |",
        f"| Vector Hit@1 (n={len(positive_test_rows)}) | {_pct(overall['hit_at_1'])} |",
        f"| Vector Hit@3 (n={len(positive_test_rows)}) | {_pct(overall['hit_at_3'])} |",
        f"| Mean reciprocal rank (MRR; n={len(positive_test_rows)}) | {_number(overall['mrr'], 4)} |",
        f"| Graph-expanded context recall (n={len(positive_test_rows)}) | {_pct(retrieval['test_graph_context_recall'])} |",
        f"| Graph recall gain over vector Hit@3 | "
        f"{_percentage_points(retrieval.get('test_graph_context_recall_gain', retrieval['test_graph_context_recall'] - overall['hit_at_3']))} |",
        f"| Mean graph-expanded context size | {_number(graph_mean)} artifacts |",
        f"| OOD detection F1 ({len(ood_test_rows)} OOD / {len(positive_test_rows) + len(ood_test_rows)} total) | {_pct(ood_test['f1'])} |",
        f"| OOD rejection rate (n={len(ood_test_rows)}) | {_pct(ood_test['recall'])} |",
        f"| Correct-and-accepted in-domain rate (n={len(positive_test_rows)}) | {_pct(accepted_top1)} |",
        f"| Database retrieval latency, p50 / p95 | "
        f"{_number(latency['p50_ms'])} / {_number(latency['p95_ms'])} ms |",
        "",
        "The cosine-distance rejection threshold was selected only on the development split "
        f"(`{selected['threshold']}`) and then applied unchanged to the test split.",
    ]


def _vision_section(vision: dict[str, Any]) -> list[str]:
    summary = vision["summary"]
    metadata = vision.get("metadata", {})
    if not metadata.get("complete", True):
        return [
            "## Landmark image recognition",
            "",
            "Incomplete benchmark: "
            f"{summary['evaluated_images']}/{metadata.get('manifest_images', 'unknown')} "
            "images have checkpointed results. Resume before reporting metrics.",
        ]
    latency = summary["latency"]
    classification = summary["recognition_classification"]
    return [
        "## Landmark image recognition",
        "",
        f"- Dataset: {summary['evaluated_images']} unique images "
        f"({summary['in_domain_images']} landmark, {summary['ood_images']} out-of-domain).",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Top-1 landmark accuracy | {_pct(summary['top_1_accuracy'])} |",
        f"| Top-3 landmark recall | {_pct(summary['top_3_recall'])} |",
        f"| In-domain vs. OOD classification F1 | {_pct(classification['f1'])} |",
        f"| Out-of-domain rejection rate | {_pct(summary['ood_rejection_rate'])} |",
        f"| Provider failure rate ({summary.get('provider_failures', 0)} failures) | "
        f"{_pct(summary['provider_failure_rate'])} |",
        f"| End-to-end latency, p50 / p95 | "
        f"{_number(latency['p50_ms'])} / {_number(latency['p95_ms'])} ms |",
    ]


def _system_section(system_results: list[dict[str, Any]]) -> list[str]:
    checks = [check for result in system_results for check in result.get("checks", [])]
    lines = ["## Engineering quality gates", ""]
    if not checks:
        return lines + ["No system checks were recorded."]
    lines.extend(["| Check | Status | Duration |", "|---|---:|---:|"])
    for check in checks:
        lines.append(
            f"| `{check['name']}` | {check['status']} | "
            f"{_number(check['duration_seconds'])} s |"
        )
    return lines


def _cv_section(
    rag: dict[str, Any] | None, vision: dict[str, Any] | None
) -> list[str]:
    lines = [
        "## CV-ready evidence (English)",
        "",
        "Use only the bullets backed by successful results in this report.",
        "",
    ]
    if rag:
        metadata = rag["metadata"]
        retrieval = rag["vector_retrieval"]
        overall = retrieval["test"]["overall"]
        ood = _ood_metrics(retrieval["ood_threshold"])
        lines.append(
            "- Designed and evaluated a bilingual RAG retrieval pipeline over "
            f"{metadata['indexed_documents']} pgvector-indexed knowledge chunks and "
            f"{metadata.get('indexed_artifacts', 'n/a')} landmarks using "
            f"{metadata['positive_queries'] + metadata['ood_queries']} labeled queries; "
            f"achieved {_pct(overall['hit_at_1'])} Hit@1, {_pct(overall['hit_at_3'])} "
            f"Hit@3, and {_pct(ood['f1'])} F1 for out-of-domain query detection on a "
            "held-out test split."
        )
    if (
        vision
        and vision.get("metadata", {}).get("complete", True)
        and float(vision["summary"].get("provider_failure_rate", 0.0)) == 0.0
    ):
        summary = vision["summary"]
        lines.append(
            "- Built and benchmarked a Gemini-based landmark recognition pipeline with "
            "image preprocessing, candidate reranking, confidence rejection, and provider "
            f"fallbacks; reached {_pct(summary['top_1_accuracy'])} top-1 accuracy and "
            f"{_pct(summary['ood_rejection_rate'])} out-of-domain rejection across "
            f"{summary['evaluated_images']} unique evaluation images."
        )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rag", type=Path, default=RESULTS_DIR / "rag_results.json")
    parser.add_argument("--vision", type=Path, default=RESULTS_DIR / "vision_results.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rag = _load(args.rag.resolve())
    vision = _load(args.vision.resolve())
    system_results = [
        result
        for path in sorted(RESULTS_DIR.glob("*system_results.json"))
        if (result := _load(path)) is not None
    ]

    lines = [
        "# AI Tour Guide Evaluation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This report separates development-time threshold calibration from held-out test "
        "metrics and records sample sizes so the results can be audited before use in a CV.",
    ]
    lines.extend(["", *(_rag_section(rag) if rag else ["## RAG and entity retrieval", "", "Not run."])])
    lines.extend(["", *(_vision_section(vision) if vision else ["## Landmark image recognition", "", "Not run."])])
    lines.extend(["", *_system_section(system_results)])
    lines.extend(["", *_cv_section(rag, vision), ""])

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
