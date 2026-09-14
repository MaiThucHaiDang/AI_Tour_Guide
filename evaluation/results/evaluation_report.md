# AI Tour Guide Evaluation Report

Generated: 2026-09-13T19:20:01.215181+00:00

This report separates development-time threshold calibration from held-out test metrics and records sample sizes so the results can be audited before use in a CV.

## RAG and entity retrieval

- Dataset: 136 labeled Vietnamese/English queries and 20 out-of-domain queries across the development/test splits.
- Index: 393 pgvector documents across 17 landmarks using `gemini-embedding-2` embeddings.
- Knowledge graph: 105 facts and 107 relations.

| Metric | Held-out test result |
|---|---:|
| Fuzzy entity-lookup accuracy (n=34) | 44.1% |
| Vector Hit@1 (n=68) | 88.2% |
| Vector Hit@3 (n=68) | 94.1% |
| Mean reciprocal rank (MRR; n=68) | 0.9069 |
| Graph-expanded context recall (n=68) | 97.1% |
| Graph recall gain over vector Hit@3 | +2.9 pp |
| Mean graph-expanded context size | 5.18 artifacts |
| OOD detection F1 (10 OOD / 78 total) | 80.0% |
| OOD rejection rate (n=10) | 100.0% |
| Correct-and-accepted in-domain rate (n=68) | 82.3% |
| Database retrieval latency, p50 / p95 | 8.08 / 10.34 ms |

The cosine-distance rejection threshold was selected only on the development split (`0.357536`) and then applied unchanged to the test split.

## Landmark image recognition

- Dataset: 43 unique images (38 landmark, 5 out-of-domain).

| Metric | Result |
|---|---:|
| Top-1 landmark accuracy | 52.6% |
| Top-3 landmark recall | 63.2% |
| In-domain vs. OOD classification F1 | 98.7% |
| Out-of-domain rejection rate | 100.0% |
| Provider failure rate (0 failures) | 0.0% |
| End-to-end latency, p50 / p95 | 3770.38 / 7997.16 ms |

## Engineering quality gates

| Check | Status | Duration |
|---|---:|---:|
| `backend_pytest` | failed | 31.90 s |
| `frontend_build` | passed | 8.20 s |
| `web_speech_tests` | passed | 0.83 s |

## CV-ready evidence (English)

Use only the bullets backed by successful results in this report.

- Designed and evaluated a bilingual RAG retrieval pipeline over 393 pgvector-indexed knowledge chunks and 17 landmarks using 156 labeled queries; achieved 88.2% Hit@1, 94.1% Hit@3, and 80.0% F1 for out-of-domain query detection on a held-out test split.
- Built and benchmarked a Gemini-based landmark recognition pipeline with image preprocessing, candidate reranking, confidence rejection, and provider fallbacks; reached 52.6% top-1 accuracy and 100.0% out-of-domain rejection across 43 unique evaluation images.
