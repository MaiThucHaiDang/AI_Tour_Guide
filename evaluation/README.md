# AI/RAG evaluation

This directory provides a reproducible, evidence-oriented benchmark for the
project's bilingual entity retrieval, pgvector RAG retrieval, landmark image
recognition, and deterministic engineering checks. Raw per-case predictions are
stored with each result so reported CV numbers can be audited.

## What is measured

- **Entity lookup:** exact/fuzzy artifact resolution accuracy in Vietnamese and
  English.
- **Vector RAG retrieval:** Hit@1, Hit@3, mean reciprocal rank (MRR), graph-expanded
  context recall, and database retrieval p50/p95 latency.
- **Out-of-domain retrieval:** a cosine-distance threshold is selected on the
  development split, then evaluated without adjustment on the held-out test split.
- **Vision:** top-1 accuracy, top-3 recall, recognition F1, out-of-domain rejection,
  provider failure rate, and end-to-end p50/p95 latency.
- **Quality gates:** backend tests, frontend production build, and Web Speech tests.

The bundled RAG set contains 136 positive bilingual queries across 17 artifacts
plus 20 out-of-domain queries. The vision manifest references 43 local images and
deduplicates identical files by SHA-256 by default. These are project-level
validation sets, not external research benchmarks; always state their sample sizes
when quoting results.

## Reproduce the evaluation

The isolated Compose file uses its own PostgreSQL/pgvector volume and does not
modify the development database. A configured `.env` with valid Gemini and Groq
credentials is required for embedding, graph construction, and vision evaluation.

Check credential/model access without printing secrets (add `--smoke` to make one
minimal embedding/generation request per configured provider key):

```powershell
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/check_provider_access.py --smoke
```

```powershell
docker compose -f evaluation/docker-compose.eval.yml up -d postgres
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator alembic upgrade head
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python scripts/seed_data.py
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python scripts/build_rag_index.py
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python scripts/build_graph.py
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/run_rag_eval.py
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/run_vision_eval.py
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/run_system_eval.py --skip-frontend --output evaluation/results/backend_system_results.json
```

Vision results are checkpointed atomically after every image. If a run is
interrupted or a provider quota is temporarily exhausted, resume it without
resending successful cases:

```powershell
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/run_vision_eval.py --resume
```

If only reporting metadata/schema changes (not the corpus, embeddings, graph, or
retrieval code), audited vector cases can be reused without another external
embedding call:

```powershell
docker compose -f evaluation/docker-compose.eval.yml run --rm evaluator python evaluation/run_rag_eval.py --reuse-vector-cases evaluation/results/rag_results.json
```

Run frontend checks on the host, where Node.js is installed:

```powershell
python evaluation/run_system_eval.py --skip-backend --output evaluation/results/frontend_system_results.json
python evaluation/generate_report.py
```

If the Windows `python` launcher is unavailable, use another installed Python 3
interpreter for the two dependency-free commands above. Generated artifacts are
written to `evaluation/results/`.

To stop the isolated database while retaining its volume:

```powershell
docker compose -f evaluation/docker-compose.eval.yml down
```

Use `down -v` only when you intentionally want to delete the evaluation database.

## Dataset structure

- `data/rag_cases.json`: manually labeled Vietnamese/English entity and semantic
  queries, with development/test assignment performed deterministically by the
  runner.
- `data/vision_manifest.json`: explicit image paths and expected artifact IDs;
  `null` denotes an out-of-domain image that should be rejected.
- `results/*.json`: full metadata, aggregate metrics, latency, and per-case outputs.
- `results/evaluation_report.md`: generated summary and evidence-backed English CV
  bullets.

Do not hand-tune thresholds on the test split. Add new development and test cases
before rerunning if the retrieval corpus, model, prompts, or rejection logic changes.
