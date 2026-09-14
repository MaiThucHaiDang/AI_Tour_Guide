from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from evaluation import run_vision_eval


@pytest.mark.asyncio
async def test_resume_reuses_valid_case_without_calling_provider(tmp_path, monkeypatch):
    relative_path = "gallery/Cuahoabinh_1.jpg"
    _, sha256 = run_vision_eval._to_data_url(
        run_vision_eval.PROJECT_ROOT / relative_path
    )
    output = tmp_path / "vision_results.json"
    output.write_text(
        json.dumps(
            {
                "metadata": {
                    "vision_model": run_vision_eval.settings.GEMINI_VISION_MODEL,
                    "complete": False,
                },
                "cases": [
                    {
                        "path": relative_path,
                        "sha256": sha256,
                        "expected_artifact_id": 1,
                        "predicted_artifact_id": 1,
                        "recognized": True,
                        "raw_label": "Cửa Hòa Bình",
                        "confidence_score": 0.9,
                        "final_score": 0.8,
                        "candidate_artifact_ids": [1],
                        "error": None,
                        "latency_ms": 100.0,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    provider = AsyncMock()
    monkeypatch.setattr(run_vision_eval, "recognize_image", provider)

    result = await run_vision_eval.run(
        run_vision_eval.DEFAULT_MANIFEST,
        output,
        delay_seconds=0.0,
        limit=1,
        deduplicate=True,
        resume=True,
    )

    provider.assert_not_awaited()
    assert result["metadata"]["complete"] is True
    assert result["summary"]["evaluated_images"] == 1
    assert result["cases"][0]["predicted_artifact_id"] == 1
