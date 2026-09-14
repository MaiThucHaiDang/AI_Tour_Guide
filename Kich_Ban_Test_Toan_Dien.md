# KỊCH BẢN KIỂM THỬ TOÀN DIỆN AI TOUR GUIDE

**Dự án:** AI Tour Guide - Kinh thành Huế / Đại Nội  
**Bản cập nhật:** 25/06/2026  
**Mục tiêu:** Chuẩn bị demo với người dùng thật, giảm rủi ro lỗi ở các luồng AI, bản đồ, giọng nói, thanh toán, blog, rating, passport và game.

Tài liệu này được viết lại dựa trên codebase hiện tại, gồm:

- Backend FastAPI trong `backend/`
- Frontend React/Vite trong `frontend/`
- Test hiện có trong `backend/tests/` và `frontend/scripts/`
- Dữ liệu ảnh demo trong `test_images/`
- Tài liệu chạy hệ thống trong `README.md`, `guideRun.md`, `docs/architecture.md`

---

## 0. Tiêu chuẩn hoàn tất trước demo

### 0.1. Definition of Done

- [ ] Toàn bộ backend unit/integration test P0 pass.
- [ ] Frontend build pass.
- [ ] Web Speech TTS test pass.
- [ ] Photo booth album test pass.
- [ ] Chạy smoke test thủ công đủ 8 luồng demo chính.
- [ ] Không còn lỗi trắng màn hình khi backend tắt, mất mạng, thiếu quyền camera/microphone.
- [ ] Không lộ API key, stack trace, traceback hoặc exception thô ở response cho người dùng.
- [ ] Không dùng database thật khi chạy automation test ghi dữ liệu.
- [ ] Có dữ liệu seed đủ 17 công trình và ảnh demo hoạt động.

### 0.2. Lệnh kiểm thử chuẩn

Chạy từ thư mục root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run build
npm run test:web-speech
npm run test:photo-booth
npm run lint
```

Nếu cần chạy backend thủ công:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Nếu cần chạy frontend:

```powershell
cd frontend
npm run dev
```

URL demo local:

- Frontend: `https://localhost:5173`
- Backend: `http://127.0.0.1:8000`
- Health: `http://127.0.0.1:8000/api/v1/health/ready`

---

## 1. Bản đồ hệ thống cần test

### 1.1. Backend

| Nhóm | File chính | Trách nhiệm | Mức ưu tiên |
|---|---|---|---|
| App shell | `backend/main.py` | FastAPI app, CORS, request id, error handler, metrics | P0 |
| Health | `backend/api/routers/health_router.py` | live/ready/deep AI health | P0 |
| Vision | `backend/api/routers/vision_router.py`, `backend/services/vision/*` | nhận diện ảnh, scoring, fallback LLM | P0 |
| Unified chat | `backend/api/routers/chat_router.py`, `backend/orchestrators/unified_orchestrator.py` | text, image, audio, memory, RAG, TTS token | P0 |
| Voice legacy | `backend/api/routers/voice_router.py`, `backend/orchestrators/voice_orchestrator.py` | voice chat, streaming SSE | P1 |
| RAG/repository | `backend/repositories/artifact_repository.py` | tìm hiện vật, fuzzy match, context DB | P0 |
| Map | `backend/api/routers/map_router.py`, `backend/services/map/*` | route, OSRM fallback, tour plan, next suggestion, calibration | P0 |
| Game | `backend/api/routers/game_router.py`, `backend/services/map/game_service.py` | phòng quiz, điểm, trạng thái, praise | P1 |
| Payment | `backend/api/routers/payment_router.py`, `backend/services/payment/vnpay_service.py` | VNPay URL, return, IPN, order info | P1 |
| Blog | `backend/api/routers/blog_router.py`, `backend/schemas/blog.py` | list/detail/create/comment/interaction | P1 |
| Rating | `backend/api/routers/rating_router.py`, `backend/schemas/rating.py` | tạo review, danh sách, summary | P1 |
| Feedback | `backend/api/routers/feedback_router.py` | lưu feedback câu trả lời AI | P0 |
| Config/security | `backend/core/config/settings.py`, `backend/core/security/rate_limit.py` | env, rate limit, production validation | P0 |

### 1.2. Frontend

| Nhóm | File chính | Trách nhiệm | Mức ưu tiên |
|---|---|---|---|
| App routing | `frontend/src/App.jsx` | view state, URL query/path, lazy preload | P0 |
| API service | `frontend/src/services/apiService.js` | gọi backend, TTS Web Speech, map/game/blog APIs | P0 |
| Chat UI | `frontend/src/components/voice/*` | composer, message list, feedback, TTS controls | P0 |
| Audio recording | `frontend/src/hooks/useAudioRecorder.js` | MediaRecorder, permission error, duration limit | P0 |
| Map UI | `frontend/src/components/map/*` | Leaflet, route, tour plan, calibration, stop sheet | P0 |
| Passport | `frontend/src/services/tourMemoryService.js`, `frontend/src/components/passport/*` | check-in, ảnh, câu hỏi, audio, summary | P1 |
| Photo booth | `frontend/src/utils/photoBoothCanvas.js`, `photoBoothCamera.js`, `PhotoBoothModal.jsx` | frame mask, camera stream, compose ảnh | P1 |
| Game UI | `frontend/src/components/game/*` | host/player, polling, answer, scoreboard | P1 |
| Payment UI | `frontend/src/components/payment/*` | checkout, food items, VNPay popup, result | P1 |
| Blog UI | `frontend/src/components/blog/*` | list/detail/editor/draft/interactions/comments | P1 |
| Rating UI | `frontend/src/components/rating/*` | star rating, submit review, summary | P1 |

---

## 2. Chiến lược test

### 2.1. Test pyramid bắt buộc

1. **Unit test:** test từng helper/function bằng mock, không gọi network thật.
2. **Router contract test:** dùng `TestClient`, override DB/session/provider.
3. **Integration test:** dùng database test riêng, migration + seed dữ liệu nhỏ.
4. **Frontend service test:** test pure JS, fetch mocked.
5. **E2E test:** Playwright/Cypress cho luồng người dùng thật.
6. **Manual demo rehearsal:** chạy đúng kịch bản demo với dữ liệu thật.
7. **Security/load test:** chỉ chạy có kiểm soát trên môi trường local/staging.

### 2.2. Quy tắc database test

- Không chạy test ghi dữ liệu vào `ai_tour_guide` thật.
- Dùng database riêng: `ai_tour_guide_test`.
- Mỗi test ghi dữ liệu phải rollback hoặc recreate schema.
- Các test router phải override `get_db_session`.
- Test map/game/blog/payment/rating không được phụ thuộc dữ liệu thật trừ nhóm smoke.

### 2.3. Quy tắc mock provider AI

- Unit test không gọi Gemini, Groq, Edge TTS, OSRM, VNPay thật.
- Mock `get_llm_provider`, `get_stt_provider`, `get_tts_provider`.
- Mock `recognize_image`, `get_artifact_by_id`, `find_artifact_by_name`.
- Chỉ health deep hoặc smoke AI mới được gọi provider thật.

### 2.4. Severity

| Mức | Ý nghĩa | Chặn demo |
|---|---|---|
| P0 | Luồng demo chính hoặc lỗi bảo mật rõ ràng | Có |
| P1 | Tính năng phụ nhưng có thể xuất hiện khi người dùng thật thao tác | Tùy mức |
| P2 | Edge case, tối ưu, khả năng mở rộng | Không nếu có workaround |

---

## 3. Test hiện có và khoảng trống

### 3.1. Test hiện có

| File | Đang cover | Nhận xét |
|---|---|---|
| `backend/tests/test_api_contract.py` | chat greeting, feedback, metrics, tiny audio, vision LLM fallback | Tốt cho contract P0, cần thêm lỗi validation |
| `backend/tests/test_unified_chatbot.py` | text/image/multimodal, memory, fallback, context compare/switch | Tốt, cần thêm TTS token, cache, vision observation |
| `backend/tests/test_voice_features.py` | language, Groq key, STT no-speech, TTS failure | Tốt, cần thêm stream size validation |
| `backend/tests/test_rag_database.py` | artifact lookup, context, canonicalization, graph search | Có phụ thuộc DB, cần test DB cô lập |
| `backend/tests/test_game_service.py` | game flow, local-ip | Cần thêm host authorization/race/time expiry |
| `backend/tests/test_vulnerabilities.py` | game validation, RAG robustness | Tốt, cần mở rộng security API |
| `backend/tests/test_tour_service.py` | plan tour, far fallback, next suggestion | Cần mock OSRM và DB |
| `frontend/scripts/webSpeechTts.test.mjs` | Web Speech queue, pause/resume/stop, long text | Rất quan trọng cho demo |
| `frontend/scripts/photoBoothAlbum.test.mjs` | memory quota, album photo separation | Tốt cho passport/photo booth |

### 3.2. Khoảng trống cần bổ sung trước demo

- [ ] `voice_chat_stream` chưa gọi `validate_audio_size(audio_bytes)` trước khi xử lý. Cần test P0 và sửa nếu fail.
- [ ] `GET /api/v1/map/config` đang trả `google_maps_api_key`. Cần test P0 không lộ key.
- [ ] `POST /api/v1/map/config` không có auth. Cần test P0 và quyết định khóa endpoint khi demo production.
- [ ] Game start/next/end ghi "host only" nhưng request không có host token. Cần test P0/P1 để chứng minh rủi ro.
- [ ] Payment chưa validate email bằng `EmailStr`; unknown food key bị tính tiền 0 thay vì reject. Cần test P1.
- [ ] Feedback không rate limit riêng. Cần test P1 nếu mở public.
- [ ] Health deep `/api/v1/health/ai` gọi provider thật, cần rate limit hoặc tắt ở production. Cần test P1.
- [ ] Frontend chưa có Vitest/React Testing Library. Cần bổ sung ít nhất service tests hoặc Playwright E2E.

---

## 4. Ma trận unit test backend theo từng hàm

Tên file test đề xuất:

- `backend/tests/unit/test_request_validation.py`
- `backend/tests/unit/test_image_utils.py`
- `backend/tests/unit/test_vision_scoring.py`
- `backend/tests/unit/test_response_generator.py`
- `backend/tests/unit/test_artifact_repository_helpers.py`
- `backend/tests/unit/test_unified_orchestrator_helpers.py`
- `backend/tests/unit/test_voice_orchestrator_helpers.py`
- `backend/tests/unit/test_map_services.py`
- `backend/tests/unit/test_game_service_unit.py`
- `backend/tests/unit/test_payment_service.py`
- `backend/tests/unit/test_blog_helpers.py`
- `backend/tests/unit/test_rating_helpers.py`

### 4.1. `backend/utils/request_validation.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `normalize_lang` | `test_normalize_lang_accepts_vi_en` | `vi`, `en` giữ nguyên |
| `normalize_lang` | `test_normalize_lang_defaults_invalid_to_vi` | `fr`, `None`, `vi-VN` trả `vi` |
| `validate_text_size` | `test_validate_text_size_allows_empty_and_limit` | Không raise |
| `validate_text_size` | `test_validate_text_size_rejects_over_limit` | HTTP 413, message có giới hạn |
| `validate_image_base64_size` | `test_validate_image_base64_size_accepts_data_url_under_limit` | Không raise |
| `validate_image_base64_size` | `test_validate_image_base64_size_rejects_estimated_large_base64` | HTTP 413 |
| `validate_audio_size` | `test_validate_audio_size_rejects_large_audio` | HTTP 413 |
| `decode_image_base64` | `test_decode_image_base64_strips_data_url` | bytes đúng |
| `decode_image_base64` | `test_decode_image_base64_rejects_invalid_payload` | `ValueError` |
| `_strip_data_url` | `test_strip_data_url_plain_and_prefixed` | Loại prefix đúng |
| `_estimate_base64_bytes` | `test_estimate_base64_bytes_padding_cases` | tính đúng padding `=`, `==` |

### 4.2. `backend/utils/image_utils.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `validate_and_preprocess_image` | `test_validate_image_accepts_jpeg_png_webp_bmp_gif` | Trả PIL Image RGB |
| `validate_and_preprocess_image` | `test_validate_image_rejects_non_image_bytes` | `ValueError` |
| `validate_and_preprocess_image` | `test_validate_image_rejects_too_small` | `ValueError` |
| `validate_and_preprocess_image` | `test_validate_image_converts_rgba_to_rgb` | mode `RGB` |
| `optimize_image_for_api` | `test_optimize_image_resizes_large_input` | width/height <= 2048 |
| `optimize_image_for_api` | `test_optimize_image_keeps_small_input` | không phóng to |
| `get_image_quality_estimate` | `test_quality_low_for_tiny_or_extreme_aspect` | score thấp |
| `get_image_quality_estimate` | `test_quality_high_for_normal_mobile_photo` | score > threshold hợp lý |

### 4.3. `backend/utils/language_manager.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `LanguageManager.__new__` | `test_language_manager_is_singleton` | 2 instance là cùng object |
| `setup_context` | `test_setup_context_vi_variants` | `vi`, `vi-VN`, `vi_VN` map DB `history_text_vi` |
| `setup_context` | `test_setup_context_en_variants` | `en`, `en-US`, `en_US` map DB `history_text_en` |
| `setup_context` | `test_setup_context_rejects_unsupported` | `ValueError` |

### 4.4. `backend/services/vision/image_recognition.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_normalize_text` | `test_vision_normalize_text_removes_accents_and_symbols` | `Điện Kiến Trung!` -> text không dấu |
| `_coerce_feature_list` | `test_coerce_feature_list_accepts_list_and_csv` | list sạch, bỏ item rỗng |
| `_coerce_candidates` | `test_coerce_candidates_uses_primary_candidate_when_no_array` | Có candidate từ label/confidence |
| `_coerce_candidates` | `test_coerce_candidates_limits_to_five` | Tối đa 5 candidates |
| `_feature_terms_for` | `test_feature_terms_for_detail_prioritizes_detail_fields` | Detail fields đứng trước |
| `_name_alias_match_score` | `test_name_alias_exact_alias_scores_one` | Score 1.0 |
| `_name_alias_match_score` | `test_name_alias_partial_overlap_scores_below_exact` | Score 0 < x <= 0.75 |
| `_visual_feature_score` | `test_visual_feature_score_matches_visible_evidence` | Score > 0 |
| `_visual_feature_score` | `test_visual_feature_score_returns_zero_without_catalog_item` | Score 0 |
| `_gps_score` | `test_gps_score_half_without_coordinates` | 0.5 |
| `_gps_score` | `test_gps_score_one_with_coordinates` | 1.0 |
| `_final_candidate_score` | `test_final_candidate_score_whole_building_weights_confidence_name_features_gps` | score trong [0,1] |
| `_final_candidate_score` | `test_final_candidate_score_detail_weights_visual_more` | detail ưu tiên visual feature |
| `_match_best_candidate` | `test_match_best_candidate_uses_repository_artifact_match` | trả artifact đúng |
| `_match_best_candidate` | `test_match_best_candidate_falls_back_legacy_mapping` | trả mapped id khi DB miss |
| `_match_best_candidate` | `test_match_best_candidate_returns_scored_candidates` | mỗi candidate có `final_score` |
| `recognize_image` | `test_recognize_image_rejects_invalid_base64` | `recognized=False`, `error=INVALID_IMAGE` |
| `recognize_image` | `test_recognize_image_rejects_non_artifact` | `NOT_AN_ARTIFACT` |
| `recognize_image` | `test_recognize_image_rejects_low_confidence` | `LOW_CONFIDENCE`, `needs_user_confirmation=True` |
| `recognize_image` | `test_recognize_image_handles_empty_provider_response` | `VISION_EMPTY_RESPONSE` |
| `recognize_image` | `test_recognize_image_handles_auth_rate_provider_errors` | lỗi map đúng `VISION_AUTH_ERROR`, `VISION_RATE_LIMITED`, `VISION_PROVIDER_UNAVAILABLE` |
| `recognize_image` | `test_recognize_image_parses_json_code_fence` | parse được ```json |
| `recognize_image` | `test_recognize_image_returns_confirmation_when_final_score_low` | recognized true nhưng `needs_user_confirmation=True` |

### 4.5. `backend/services/vision/response_generator.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_get_text_client` | `test_get_text_client_requires_gemini_key` | thiếu key raise RuntimeError |
| `_make_cache_key` | `test_make_cache_key_changes_by_artifact_lang_question` | key khác nhau |
| `_manage_cache_size` | `test_manage_cache_size_evicts_oldest_twenty_percent` | cache <= max |
| `generate_response` | `test_generate_response_returns_cached_result` | không gọi Gemini lần 2 |
| `generate_response` | `test_generate_response_retries_empty_response` | retry trước khi fail |
| `generate_response` | `test_generate_response_retries_429_timeout_then_success` | success sau retry |
| `generate_response` | `test_generate_response_raises_non_retryable_error` | raise ngay hoặc sau logic hiện tại |
| `generate_response` | `test_generate_response_uses_configured_model_name` | model đúng settings |

### 4.6. `backend/repositories/artifact_repository.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_normalize_text` | `test_repo_normalize_text_removes_vietnamese_diacritics` | normalize đúng |
| `_canonical_tokens` | `test_canonical_tokens_removes_noise_and_splits` | token list đúng |
| `_replace_canonical_phrases` | `test_replace_canonical_phrases_exact` | thay cụm đúng |
| `_replace_fuzzy_canonical_phrases` | `test_replace_fuzzy_canonical_phrases_near_sound` | sửa lỗi gần âm |
| `_replace_token_window` | `test_replace_token_window_exact_sequence` | thay đúng sequence |
| `_replace_fuzzy_token_window` | `test_replace_fuzzy_token_window_handles_missing_diacritics` | thay fuzzy |
| `_replace_canonical_tokens` | `test_replace_canonical_tokens_exact` | token chính tả đúng |
| `_replace_fuzzy_canonical_tokens` | `test_replace_fuzzy_canonical_tokens_near_sound` | token gần âm đúng |
| `_is_fuzzy_phrase_match` | `test_is_fuzzy_phrase_match_threshold` | true/false đúng |
| `_is_fuzzy_token_match` | `test_is_fuzzy_token_match_short_token_strict` | token ngắn không match sai |
| `_token_similarity` | `test_token_similarity_range` | 0..1 |
| `_levenshtein_distance` | `test_levenshtein_distance_known_pairs` | `kitten/sitting` = 3 |
| `_tokenize_query` | `test_tokenize_query_filters_short_noise` | token đúng |
| `canonicalize_transcript_entities` | `test_canonicalize_transcript_entities_fix_ngo_mon_hue` | sửa `ngo mon hue` |
| `find_artifact_by_name` | `test_find_artifact_by_name_exact_vi_en` | tìm đúng |
| `find_artifact_by_name` | `test_find_artifact_by_name_fuzzy_accentless` | tìm `dien kien trung` |
| `get_artifact_context` | `test_get_artifact_context_returns_no_match_message` | không 500 khi miss |
| `get_artifact_context_by_id` | `test_get_artifact_context_by_id_invalid_id` | fallback rõ ràng |
| `graph_augmented_search` | `test_graph_augmented_search_returns_top_k_and_facts` | số lượng <= top_k |

### 4.7. `backend/orchestrators/unified_orchestrator.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `process_chat_request` | `test_process_chat_text_small_talk_avoids_llm` | `answer_source=template`, no TTS token |
| `process_chat_request` | `test_process_chat_text_artifact_match_loads_context` | trả artifact id/name |
| `process_chat_request` | `test_process_chat_audio_tiny_not_heard` | không init STT, message chưa nghe rõ |
| `process_chat_request` | `test_process_chat_audio_transcribes_and_canonicalizes` | transcript canonical |
| `process_chat_request` | `test_process_chat_audio_stt_timeout_cleans_task` | không treo |
| `process_chat_request` | `test_process_chat_image_success_sets_artifact_context` | vision step, artifact info |
| `process_chat_request` | `test_process_chat_image_unrecognized_without_text_returns_template` | không gọi LLM |
| `process_chat_request` | `test_process_chat_image_unrecognized_with_text_keeps_user_question` | LLM nhận context ảnh không nhận diện |
| `process_chat_request` | `test_process_chat_image_provider_timeout_with_preselected_artifact_continues` | dùng `artifact_id` đang chọn |
| `process_chat_request` | `test_process_chat_multimodal_prefers_text_question_with_image_context` | transcript là text user |
| `process_chat_request` | `test_process_chat_loads_active_artifact_from_memory` | lấy context_data artifact_id |
| `process_chat_request` | `test_process_chat_context_switch_updates_primary` | switch sang artifact mới |
| `process_chat_request` | `test_process_chat_context_compare_keeps_primary_and_adds_comparative` | context primary + comparative |
| `process_chat_request` | `test_process_chat_cache_hit_avoids_llm` | `answer_source=cache` |
| `process_chat_request` | `test_process_chat_multi_artifacts_returns_joined_summaries` | `answer_source=db_direct` |
| `process_chat_request` | `test_process_chat_llm_failure_with_artifact_returns_wrapped_summary` | không crash |
| `process_chat_request` | `test_process_chat_llm_failure_without_context_returns_resilient_fallback` | message thân thiện |
| `process_chat_request` | `test_process_chat_creates_tts_token_for_llm_answer` | `tts_token` có 24 chars |
| `_finalize_without_tts` | `test_finalize_without_tts_saves_memory_and_steps` | memory user/assistant |
| `_classify_context_intent` | `test_classify_context_intent_compare_keywords` | trả `COMPARE_OR_REFER` |
| `_classify_context_intent` | `test_classify_context_intent_defaults_switch` | trả `SWITCH` |
| `_classify_query_type` | `test_classify_query_type_intro_for_marker_prompt` | `intro` |
| `_classify_query_type` | `test_classify_query_type_followup_for_fact_question` | `followup` |
| `_get_llm` | `test_get_llm_uses_factory_lazily` | factory gọi 1 lần |
| `_get_tts` | `test_get_tts_returns_none_without_factory` | None |
| `_build_direct_answer` | `test_build_direct_answer_year_author_location` | trả câu trực tiếp cho câu hỏi năm/tác giả/ở đâu |
| `_build_artifact_description` | `test_build_artifact_description_marker_intro_uses_intro_cache` | cache intro |
| `_generate_intro` | `test_generate_intro_uses_voice_prompt_and_sanitizes` | prompt đúng |
| `_wrapped_summary` | `test_wrapped_summary_vi_en_and_missing_history` | fallback khi thiếu history |
| `_find_multi_artifacts` | `test_find_multi_artifacts_with_va_and_and_separators` | >=2 artifact |
| `_build_small_talk_answer` | `test_small_talk_greeting_thanks_vi_en` | trả template |
| `_build_general_context` | `test_build_general_context_includes_history` | có history |
| `_build_resilient_fallback_answer` | `test_resilient_fallback_differs_by_context_and_lang` | message đúng |
| `_not_heard_message` | `test_not_heard_message_vi_en` | message đúng |
| `_unrecognized_image_message` | `test_unrecognized_image_message_vi_en` | message đúng |
| `_has_image_observation` | `test_has_image_observation_detects_visual_fields` | true nếu có visual summary/features |
| `_build_image_fallback_answer` | `test_image_fallback_uses_visual_context_before_generic` | có chi tiết ảnh |
| `_sanitize_user_response` | `test_sanitize_user_response_removes_internal_prompt_labels` | không còn `DB_CONTEXT`, `USER_QUESTION` |
| `_format_vision_analysis` | `test_format_vision_analysis_includes_candidates_and_requirement` | context ảnh đầy đủ |
| `_format_artifact_context` | `test_format_artifact_context_includes_optional_fields` | visit highlights, route, nearby |
| `_artifact_name` | `test_artifact_name_by_lang` | đúng ngôn ngữ |
| `_short_summary` | `test_short_summary_truncates_cleanly` | ngắn, không empty nếu có history |
| `_normalize_text` | `test_unified_normalize_text_keeps_bracket_tokens` | normalize đúng |
| `_cache_key` | `test_cache_key_uses_lang_artifact_query` | key ổn định |
| `_get_cached_answer/_set_cached_answer` | `test_answer_cache_evicts_oldest_at_limit` | không vượt max |
| `_step_label` | `test_step_label_vi_en_and_unknown` | label đúng |
| `_make_tts_token` | `test_make_tts_token_deterministic_and_lang_sensitive` | deterministic |
| `_build_speech_text` | `test_build_speech_text_truncates_by_sentence` | <= max_chars |
| `_background_tts` | `test_background_tts_sets_ready_or_failed` | cache status đúng |
| `fetch_tts_status` | `test_fetch_tts_status_pending_ready_expired` | trạng thái đúng |
| `fetch_tts_audio` | `test_fetch_tts_audio_only_returns_when_ready` | bytes hoặc None |
| `_evict_tts_cache` | `test_evict_tts_cache_removes_expired_or_oldest` | cache giới hạn |

### 4.8. `backend/orchestrators/voice_orchestrator.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `process_voice_request` | `test_voice_process_tiny_audio_not_heard` | không gọi STT/LLM |
| `process_voice_request` | `test_voice_process_stt_db_llm_tts_success` | transcript, response, audio bytes |
| `process_voice_request` | `test_voice_process_prefetched_context_overrides_lookup` | dùng context đã prefetch |
| `process_voice_request` | `test_voice_process_no_db_context_returns_no_context_message` | không bịa |
| `process_voice_request` | `test_voice_process_llm_failure_returns_fallback_audio` | vẫn có text/audio nếu TTS ok |
| `process_voice_request` | `test_voice_process_tts_failure_keeps_text` | không mất response text |
| `process_voice_request_stream` | `test_voice_stream_yields_transcript_text_audio_chunks` | SSE chunk đúng type |
| `process_voice_request_stream` | `test_voice_stream_provider_error_yields_error_chunk_without_traceback` | không lộ traceback |
| `_call_db_lookup` | `test_call_db_lookup_accepts_sync_and_async_lookup` | đều chạy |
| `_is_unhelpful_context` | `test_is_unhelpful_context_detects_no_match` | true |
| `_classify_intent` | `test_voice_classify_intent_general_fact_intro` | intent đúng |
| `_normalize_text` | `test_voice_normalize_text` | normalize tiếng Việt |
| `_synthesize_response` | `test_synthesize_response_returns_empty_on_tts_failure_or_raises_expected` | behavior rõ |

### 4.9. `backend/services/memory/conversation_memory.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `add_turn` | `test_memory_add_turn_ignores_empty_session_or_content` | không ghi DB |
| `add_turn` | `test_memory_add_turn_truncates_long_content` | content kết thúc `...` |
| `format_history` | `test_memory_format_history_orders_old_to_new` | label User/Assistant đúng |
| `get_recent_context` | `test_memory_get_recent_context_returns_latest_limit_in_chronological_order` | đúng thứ tự |
| `clear` | `test_memory_clear_deletes_session_only` | session khác không bị xóa |
| `_role_label` | `test_memory_role_label_assistant_aliases` | label đúng |

### 4.10. `backend/services/map/osrm_service.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `get_route` | `test_osrm_get_route_success_converts_lng_lat_to_lat_lng` | coordinates Leaflet đúng |
| `get_route` | `test_osrm_get_route_non_ok_returns_false` | success false |
| `get_route` | `test_osrm_get_route_http_error_returns_false` | không raise |
| `_parse_steps` | `test_parse_steps_vi_en` | instruction đúng ngôn ngữ |
| `_translate_step_vi` | `test_translate_step_vi_depart_left_right_straight_arrive` | text đúng |
| `_translate_step_en` | `test_translate_step_en_depart_left_right_straight_arrive` | text đúng |

### 4.11. `backend/services/map/routing.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_load_graph` | `test_load_graph_missing_file_keeps_empty_graph` | không crash |
| `_load_graph` | `test_load_graph_valid_json_adds_nodes_edges` | số node/edge đúng |
| `find_nearest_node` | `test_find_nearest_node_empty_graph_returns_none` | None |
| `find_nearest_node` | `test_find_nearest_node_returns_closest` | node đúng |
| `calculate_route` | `test_calculate_route_empty_graph_fails` | success false |
| `calculate_route` | `test_calculate_route_same_nearest_node_returns_arrived` | instruction đã ở gần |
| `calculate_route` | `test_calculate_route_shortest_path_success` | path, coordinates, instructions |
| `calculate_route` | `test_calculate_route_no_path_returns_message` | success false |
| `_generate_instructions` | `test_generate_instructions_empty_and_path` | có bắt đầu/kết thúc |

### 4.12. `backend/services/map/tour_service.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `haversine_distance` | `test_haversine_distance_zero_and_known_meter_range` | 0 và xấp xỉ đúng |
| `is_far_from_hue` | `test_is_far_from_hue_true_for_saigon_false_for_citadel` | boolean đúng |
| `plan_tour` | `test_plan_tour_uses_ngo_mon_when_start_far` | `is_start_far=True` |
| `plan_tour` | `test_plan_tour_no_artifacts_returns_failure` | success false |
| `plan_tour` | `test_plan_tour_filters_missing_coordinates` | không chọn missing coords |
| `plan_tour` | `test_plan_tour_respects_max_places` | route <= max_places |
| `plan_tour` | `test_plan_tour_allows_first_stop_even_when_budget_short` | vẫn có 1 stop |
| `plan_tour` | `test_plan_tour_osrm_failure_uses_straight_line_fallback` | có coords/instructions |
| `get_next_suggestion` | `test_next_suggestion_empty_db_returns_empty` | [] |
| `get_next_suggestion` | `test_next_suggestion_excludes_current_and_visited` | không có id đã đi |
| `get_next_suggestion` | `test_next_suggestion_relation_boost_affects_order` | relation weight tăng score |
| `get_next_suggestion` | `test_next_suggestion_returns_top_three_with_reason` | <=3, có reason |

### 4.13. `backend/services/map/game_service.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `GameRoom.__init__` | `test_game_room_adds_host_player_when_host_nickname_present` | host trong players |
| `GameRoom.to_dict` | `test_game_room_to_dict_hides_answers_in_playing` | không lộ correct answer |
| `GameRoom.to_dict` | `test_game_room_to_dict_shows_answer_on_scoreboard` | có `correct_option_index` |
| `generate_room_code` | `test_generate_room_code_unique_uppercase_four_chars` | không trùng active rooms |
| `create_room` | `test_create_room_rejects_empty_visited_ids` | ValueError |
| `create_room` | `test_create_room_rejects_empty_or_long_host_name` | ValueError |
| `create_room` | `test_create_room_fetches_artifacts_and_facts` | prompt có facts |
| `create_room` | `test_create_room_parses_json_code_block` | questions đúng |
| `create_room` | `test_create_room_fallback_questions_on_bad_llm_json` | fallback list |
| `create_room` | `test_create_room_validates_question_shape` | đề xuất bổ sung validation 4 options |
| `_get_fallback_questions` | `test_fallback_questions_vi_en` | text đúng lang |
| `join_room` | `test_join_room_rejects_missing_room_non_lobby_duplicate_long_empty` | ValueError đúng |
| `start_game` | `test_start_game_requires_lobby_and_players` | state playing |
| `submit_answer` | `test_submit_answer_scores_correct_fast_answer` | score 500..1000 |
| `submit_answer` | `test_submit_answer_no_score_after_time_limit` | score 0 |
| `submit_answer` | `test_submit_answer_rejects_wrong_question_unknown_player_duplicate` | ValueError |
| `submit_answer` | `test_submit_answer_moves_scoreboard_when_all_answered` | status scoreboard |
| `next_question` | `test_next_question_playing_to_scoreboard` | status scoreboard |
| `next_question` | `test_next_question_scoreboard_to_next_or_finished` | index/status đúng |
| `end_game` | `test_end_game_sets_finished` | status finished |
| `get_room_status` | `test_get_room_status_auto_scoreboard_after_timer` | hết giờ tự scoreboard |
| `generate_ai_praise` | `test_generate_ai_praise_requires_finished_and_caches_result` | gọi LLM 1 lần |

### 4.14. `backend/services/payment/vnpay_service.py`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_strip_vietnamese` | `test_strip_vietnamese_removes_diacritics_and_d` | đúng |
| `_generate_order_code` | `test_generate_order_code_format_and_uniqueness` | `VNP-YYYYMMDD-HHMMSS-XXXXXX` |
| `_build_order_desc` | `test_build_order_desc_includes_ticket_and_items` | text đủ |
| `create_payment_url` | `test_create_payment_url_amount_x100_and_signature` | params đúng |
| `create_payment_url` | `test_create_payment_url_strips_special_chars_in_order_info` | không ký tự lạ |
| `verify_return_params` | `test_verify_return_params_valid_signature` | true |
| `verify_return_params` | `test_verify_return_params_rejects_missing_or_tampered_hash` | false |

### 4.15. `backend/schemas/payment.py`

| Model/hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `ItemSelection` | `test_item_selection_quantity_bounds` | ge 0, le 50 |
| `PaymentCreateRequest.validate_location` | `test_payment_request_rejects_unknown_location` | validation error |
| `PaymentCreateRequest.validate_phone` | `test_payment_request_rejects_bad_phone` | validation error |
| `PaymentCreateRequest` | `test_payment_request_should_reject_bad_email` | hiện có thể fail, cần chuyển `customer_email` sang `EmailStr` |
| `PaymentCreateRequest.calc_total` | `test_calc_total_ngo_mon_adult_child_food` | tổng đúng |
| `PaymentCreateRequest.calc_total` | `test_calc_total_dien_long_an_ignores_paid_child_ticket` | đúng policy |
| `PaymentCreateRequest.calc_total` | `test_calc_total_should_reject_unknown_food_key` | hiện có thể fail, cần validator |
| `PaymentInfo.parse_items` | `test_payment_info_parse_items_json_string_and_bad_json` | list hoặc [] |

### 4.16. `backend/api/routers/blog_router.py` và `backend/schemas/blog.py`

| Hàm/model | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `_clean_plain_text` | `test_clean_plain_text_trims_title_and_removes_null` | sạch |
| `_clean_plain_text` | `test_clean_plain_text_rejects_script_javascript_onerror` | ValueError |
| `_validate_public_url` | `test_validate_public_url_accepts_http_https_rooted_asset` | pass |
| `_validate_public_url` | `test_validate_public_url_rejects_protocol_relative_and_traversal` | ValueError |
| `BlogPostCreate.validate_tags` | `test_blog_tags_dedupe_and_reject_unsupported` | unique tags |
| `_estimate_reading_time` | `test_estimate_reading_time_min_one_and_ceil` | đúng |
| `_slugify` | `test_slugify_vietnamese_title` | slug ASCII |
| `_safe_datetime` | `test_safe_datetime_fallback_now` | datetime |
| `_build_unique_slug` | `test_build_unique_slug_appends_suffix` | `slug`, `slug-2`, `slug-3` |
| `_comment_to_response` | `test_comment_to_response_fields` | mapping đúng |
| `_post_to_summary` | `test_post_to_summary_counts_non_negative` | không âm |
| `_post_to_detail` | `test_post_to_detail_includes_comments` | có comments |
| `_get_published_post` | `test_get_published_post_404_for_missing_or_draft` | HTTP 404 |

### 4.17. `backend/api/routers/rating_router.py` và `backend/schemas/rating.py`

| Hàm/model | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `RatingCreateRequest` | `test_rating_request_bounds_1_to_5` | reject 0/6 |
| `RatingCreateRequest.clean_name` | `test_rating_clean_name_defaults_guest` | empty -> `Khách` |
| `_rating_to_response` | `test_rating_to_response_alias_fields` | camelCase response |
| `create_rating` | `test_create_rating_404_missing_location` | 404 |
| `list_location_ratings` | `test_list_ratings_pagination_bounds` | page/perPage đúng |
| `get_location_rating_summary` | `test_rating_summary_zero_when_no_ratings` | avg 0, total 0 |
| `get_location_rating_summary` | `test_rating_summary_rounds_one_decimal` | round đúng |

### 4.18. `backend/main.py`, middleware, metrics, config

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `lifespan` | `test_lifespan_continues_when_cache_setup_fails` | app vẫn start |
| `http_exception_handler` | `test_http_exception_handler_maps_413_429_500_codes` | error_code đúng |
| `request_id_middleware` | `test_request_id_middleware_reuses_or_generates_request_id` | header có `x-request-id` |
| `metrics_snapshot` | `test_metrics_snapshot_shape` | counters/durations |
| `Settings.validate_runtime` | `test_settings_validate_runtime_requires_keys_only_in_production` | dev không fail, prod fail |
| `rate_limit_exceeded_handler` | `test_rate_limit_handler_shape` | JSON shape thống nhất |
| `global_exception_handler` | `test_global_exception_handler_hides_traceback` | không lộ stack |

---

## 5. Backend API và integration test

Tên file đề xuất:

- `backend/tests/api/test_health_api.py`
- `backend/tests/api/test_vision_api.py`
- `backend/tests/api/test_chat_api.py`
- `backend/tests/api/test_voice_api.py`
- `backend/tests/api/test_map_api.py`
- `backend/tests/api/test_game_api.py`
- `backend/tests/api/test_payment_api.py`
- `backend/tests/api/test_blog_api.py`
- `backend/tests/api/test_rating_api.py`
- `backend/tests/api/test_feedback_api.py`
- `backend/tests/security/test_public_api_security.py`

### 5.1. Health và metrics

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-HEALTH-01 | `GET /api/v1/health` | gọi bình thường | 200, `status=ok` |
| API-HEALTH-02 | `GET /api/v1/health/live` | gọi bình thường | 200 |
| API-HEALTH-03 | `GET /api/v1/health/ready` | DB ok, Gemini key có | 200, checks ok/configured |
| API-HEALTH-04 | `GET /api/v1/health/ready` | mock DB fail | 503, `database=unavailable` |
| API-HEALTH-05 | `GET /api/v1/health/ready` | thiếu `GEMINI_API_KEY` | 503, `gemini_api_key=missing` |
| API-HEALTH-06 | `GET /api/v1/health/ai` | provider mocked ok | 200 `healthy` |
| API-HEALTH-07 | `GET /api/v1/health/ai` | provider fail | 503 `degraded`, không traceback |
| API-HEALTH-08 | `GET /api/v1/metrics` | sau vài request | có counter `http.200` |

### 5.2. Vision API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-VIS-01 | `POST /api/v1/recognize` | ảnh Ngọ Môn hợp lệ | success true, artifact id/name, response_text |
| API-VIS-02 | `POST /api/v1/recognize` | invalid `lang=fr` | 422 vì schema chỉ nhận `vi/en` |
| API-VIS-03 | `POST /api/v1/recognize` | lat > 90 hoặc lng > 180 | 422 hoặc 400 |
| API-VIS-04 | `POST /api/v1/recognize` | base64 lớn hơn limit | 413 `PAYLOAD_TOO_LARGE` |
| API-VIS-05 | `POST /api/v1/recognize` | model trả `NOT_AN_ARTIFACT` | success false, message thân thiện |
| API-VIS-06 | `POST /api/v1/recognize` | `LOW_CONFIDENCE` | success false, hướng dẫn chụp lại |
| API-VIS-07 | `POST /api/v1/recognize` | artifact id không có trong DB | success false, `DB_NOT_FOUND` |
| API-VIS-08 | `POST /api/v1/recognize` | nhận diện ok nhưng LLM fail | success true, `error_code=LLM_UNAVAILABLE` |
| API-VIS-09 | `POST /api/v1/recognize` | có `session_id` | memory được ghi user/assistant |
| API-VIS-10 | `POST /api/v1/recognize` | bắn quá rate limit | 429 shape thống nhất |

### 5.3. Unified chat API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-CHAT-01 | `POST /api/v1/chat/unified` | text greeting | 200, `answer_source=template`, no audio_base64 |
| API-CHAT-02 | `POST /api/v1/chat/unified` | text về artifact | artifact fields có id/name/year/author/summary |
| API-CHAT-03 | `POST /api/v1/chat/unified` | text > `TEXT_MAX_CHARS` | 413 |
| API-CHAT-04 | `POST /api/v1/chat/unified` | `session_id` > 255 | 400 |
| API-CHAT-05 | `POST /api/v1/chat/unified` | lat/lng out of range | 400 |
| API-CHAT-06 | `POST /api/v1/chat/unified` | `artifact_id <= 0` | 400 |
| API-CHAT-07 | `POST /api/v1/chat/unified` | tiny audio | 200, message chưa nghe rõ, không init STT |
| API-CHAT-08 | `POST /api/v1/chat/unified` | audio lớn hơn limit | 413 |
| API-CHAT-09 | `POST /api/v1/chat/unified` | audio đủ lớn nhưng thiếu STT provider | 503 |
| API-CHAT-10 | `POST /api/v1/chat/unified` | image + text | câu trả lời bám chi tiết ảnh trước, không generic |
| API-CHAT-11 | `POST /api/v1/chat/unified` | image fail + artifact_id có sẵn | vẫn trả lời theo artifact context |
| API-CHAT-12 | `POST /api/v1/chat/unified` | LLM fail | response fallback, không 500 |
| API-CHAT-13 | `GET /api/v1/tts/fetch` | token rỗng/quá dài | 400 |
| API-CHAT-14 | `GET /api/v1/tts/fetch` | token pending | `{status: pending}` |
| API-CHAT-15 | `GET /api/v1/tts/fetch` | token ready | audio_base64, mime |
| API-CHAT-16 | `GET /api/v1/tts/fetch` | token failed/expired | status và message rõ |

### 5.4. Voice API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-VOICE-01 | `POST /api/v1/voice/chat` | audio vi hợp lệ | transcript, response_text, audio_base64 |
| API-VOICE-02 | `POST /api/v1/voice/chat` | audio quá lớn | 413 |
| API-VOICE-03 | `POST /api/v1/voice/chat` | thiếu provider | 503 |
| API-VOICE-04 | `POST /api/v1/voice/chat` | artifact_id có sẵn | prefetch context |
| API-VOICE-05 | `POST /api/v1/voice/chat/stream` | audio hợp lệ | SSE chunks text/audio |
| API-VOICE-06 | `POST /api/v1/voice/chat/stream` | audio quá lớn | P0: phải 413. Hiện cần bổ sung `validate_audio_size` |
| API-VOICE-07 | `POST /api/v1/voice/chat/stream` | stream error | chunk error không chứa traceback/raw secret |
| API-VOICE-08 | `POST /api/v1/voice/chat/stream` | client disconnect | server dọn generator/provider task |

### 5.5. Map API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-MAP-01 | `GET /api/v1/map/route` | OSRM success | coordinates/instructions |
| API-MAP-02 | `GET /api/v1/map/route` | OSRM fail, local graph success | vẫn success |
| API-MAP-03 | `GET /api/v1/map/route` | OSRM + graph fail | 400 |
| API-MAP-04 | `GET /api/v1/map/route` | tọa độ ngoài [-90,90]/[-180,180] | nên 422/400, bổ sung nếu chưa có |
| API-MAP-05 | `GET /api/v1/map/config` | DB có artifacts | trả map_bounds và artifacts |
| API-MAP-06 | `GET /api/v1/map/config` | calibrated file corrupt | không 500, fallback default |
| API-MAP-07 | `GET /api/v1/map/config` | production/security | P0: không trả `google_maps_api_key` |
| API-MAP-08 | `POST /api/v1/map/config` | save hợp lệ | DB update, file backup update |
| API-MAP-09 | `POST /api/v1/map/config` | unauthenticated public | P0: phải 401/403 nếu production |
| API-MAP-10 | `POST /api/v1/map/config` | file write fail sau DB commit | phải rollback hoặc báo rủi ro atomicity |
| API-MAP-11 | `GET /api/v1/map/plan-tour` | gần Huế | route <= max_places |
| API-MAP-12 | `GET /api/v1/map/plan-tour` | xa Huế | fallback Ngọ Môn, `is_start_far=True` |
| API-MAP-13 | `GET /api/v1/map/plan-tour` | `max_duration=999999`, `max_places=500` | P0/P1: phải có upper bound |
| API-MAP-14 | `GET /api/v1/map/next-suggestion` | visited_ids valid | top 3, exclude visited/current |
| API-MAP-15 | `GET /api/v1/map/next-suggestion` | visited_ids invalid `1,a` | 400 |

### 5.6. Game API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-GAME-01 | `POST /api/v1/game/create` | visited_ids hợp lệ, host nickname | room code 4 chars, host player |
| API-GAME-02 | `POST /api/v1/game/create` | visited_ids rỗng | 400 |
| API-GAME-03 | `POST /api/v1/game/create` | host name rỗng/dài | 400 |
| API-GAME-04 | `POST /api/v1/game/join` | join hợp lệ | success |
| API-GAME-05 | `POST /api/v1/game/join` | room sai, name trống/dài/trùng | 400 |
| API-GAME-06 | `POST /api/v1/game/start` | chưa có player | 400 |
| API-GAME-07 | `POST /api/v1/game/start` | player khác host gọi start | P0/P1: phải 403 nếu có host token |
| API-GAME-08 | `POST /api/v1/game/answer` | answer đúng nhanh | score > 500 |
| API-GAME-09 | `POST /api/v1/game/answer` | answer sai | score 0 |
| API-GAME-10 | `POST /api/v1/game/answer` | double submit | 400 |
| API-GAME-11 | `POST /api/v1/game/next` | non-host gọi next | P0/P1: phải 403 nếu có host token |
| API-GAME-12 | `POST /api/v1/game/end` | non-host gọi end | P0/P1: phải 403 nếu có host token |
| API-GAME-13 | `GET /api/v1/game/room/{code}/status` | timer hết | status scoreboard |
| API-GAME-14 | `GET /api/v1/game/room/{code}/praise` | game chưa finished | 400 |
| API-GAME-15 | `GET /api/v1/game/local-ip` | production | P1: phải tắt hoặc chỉ dev |

### 5.7. Payment API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-PAY-01 | `GET /api/v1/payment/food-items` | gọi bình thường | trả đủ key/name/price/image |
| API-PAY-02 | `POST /api/v1/payment/create` | Ngọ Môn 1 adult, 1 child, food | amount đúng, paymentUrl có signature |
| API-PAY-03 | `POST /api/v1/payment/create` | Điện Long An childrenPaid > 0 | không cộng vé trẻ em nếu policy miễn phí |
| API-PAY-04 | `POST /api/v1/payment/create` | location không hợp lệ | 422 hoặc 400 |
| API-PAY-05 | `POST /api/v1/payment/create` | adultCount 0 | 422 |
| API-PAY-06 | `POST /api/v1/payment/create` | email `abc@.com` | P1: nên 422 sau khi dùng `EmailStr` |
| API-PAY-07 | `POST /api/v1/payment/create` | unknown food key | P1: nên 422 thay vì tính 0 |
| API-PAY-08 | `GET /api/v1/payment/return` | thiếu signature | success false |
| API-PAY-09 | `GET /api/v1/payment/return` | signature giả | success false |
| API-PAY-10 | `GET /api/v1/payment/return` | order không tồn tại | success false |
| API-PAY-11 | `GET /api/v1/payment/return` | response code 00 | order status success |
| API-PAY-12 | `GET /api/v1/payment/ipn` | signature giả | RspCode 97 |
| API-PAY-13 | `GET /api/v1/payment/ipn` | order đã processed | RspCode 02 |
| API-PAY-14 | `GET /api/v1/payment/info/{order_code}` | order có items JSON | response camelCase đúng |
| API-PAY-15 | `GET /api/v1/payment/info/{order_code}` | missing order | 404 |

### 5.8. Blog API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-BLOG-01 | `GET /api/v1/blog-posts` | list published | total, posts |
| API-BLOG-02 | `GET /api/v1/blog-posts` | search SQL injection string | không 500, không bypass |
| API-BLOG-03 | `GET /api/v1/blog-posts` | unsupported tag | 400 |
| API-BLOG-04 | `GET /api/v1/blog-posts/{slug}` | existing published | post detail + comments |
| API-BLOG-05 | `GET /api/v1/blog-posts/{slug}` | draft/missing | 404 |
| API-BLOG-06 | `POST /api/v1/blog-posts` | bài hợp lệ | 201, slug unique |
| API-BLOG-07 | `POST /api/v1/blog-posts` | title > 220 | 422 |
| API-BLOG-08 | `POST /api/v1/blog-posts` | `<script>` trong content | 422 |
| API-BLOG-09 | `POST /api/v1/blog-posts` | cover URL `//evil.com` hoặc `../x` | 422 |
| API-BLOG-10 | `POST /api/v1/blog-posts/{slug}/comments` | comment hợp lệ | 201, count tăng |
| API-BLOG-11 | `POST /api/v1/blog-posts/{slug}/comments` | comment chứa `onerror=` | 422 |
| API-BLOG-12 | `POST /api/v1/blog-posts/{slug}/interactions` | like active true/false | count tăng/giảm không âm |
| API-BLOG-13 | `POST /api/v1/blog-posts/{slug}/interactions` | action invalid | 422 |

### 5.9. Rating API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-RATE-01 | `POST /api/v1/ratings` | location có tồn tại, 3 rating | 201 |
| API-RATE-02 | `POST /api/v1/ratings` | location không tồn tại | 404 |
| API-RATE-03 | `POST /api/v1/ratings` | rating 0 hoặc 6 | 422 |
| API-RATE-04 | `POST /api/v1/ratings` | review > 2000 | 422 |
| API-RATE-05 | `GET /api/v1/ratings/location/{id}` | pagination | total + ratings đúng |
| API-RATE-06 | `GET /api/v1/ratings/location/{id}?perPage=100` | over max | 422 |
| API-RATE-07 | `GET /api/v1/ratings/location/{id}/summary` | no ratings | avg 0, total 0 |
| API-RATE-08 | `GET /api/v1/ratings/location/{id}/summary` | nhiều ratings | avg round 1 decimal |

### 5.10. Feedback API

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| API-FB-01 | `POST /api/v1/feedback` | helpful | 200, feedback_id |
| API-FB-02 | `POST /api/v1/feedback` | not_helpful + comment | 200 |
| API-FB-03 | `POST /api/v1/feedback` | rating invalid | 422 |
| API-FB-04 | `POST /api/v1/feedback` | comment > 500 | 422 |
| API-FB-05 | `POST /api/v1/feedback` | DB commit fail | 503, rollback |
| API-FB-06 | `POST /api/v1/feedback` | spam 100 req/phút | P1: nên 429 hoặc có protection |

---

## 6. Frontend unit/service test

Hiện frontend chưa có Vitest/React Testing Library. Với code hiện tại, có thể giữ pure Node script cho service thuần, hoặc bổ sung Vitest để test component/hook.

Tên file đề xuất:

- `frontend/scripts/apiService.test.mjs`
- `frontend/scripts/tourMemoryService.test.mjs`
- `frontend/scripts/photoBoothCanvas.test.mjs`
- `frontend/scripts/photoBoothCamera.test.mjs`
- `frontend/scripts/blogLocalStorage.test.mjs`
- `frontend/scripts/passportDisplayUtils.test.mjs`
- `frontend/scripts/imageUtils.test.mjs`
- Nếu thêm Vitest: `frontend/src/**/*.test.jsx`

### 6.1. `frontend/src/services/apiService.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `recognizeArtifactAPI` | `test_recognize_api_success_maps_backend_fields` | `{status: success, data}` đúng |
| `recognizeArtifactAPI` | `test_recognize_api_backend_error_returns_status_error` | không throw khi response ok nhưng success false |
| `recognizeArtifactAPI` | `test_recognize_api_http_error_throws_network_error` | throw `NETWORK_ERROR` |
| `playTTS` | đã có test 1, 6, 11, 13b, 18, 21 | giữ nguyên |
| `stopTTS` | đã có test 4, 5, 8, 16 | giữ nguyên |
| `pauseTTS/resumeTTS` | đã có test 2, 3, 14, 15, 18, 20 | giữ nguyên |
| `fetchTTSAudio` | `test_fetch_tts_audio_ready_returns_blob` | Blob đúng mime |
| `fetchTTSAudio` | `test_fetch_tts_audio_pending_error_failed` | status đúng |
| `voiceChatAPI` | `test_voice_chat_api_builds_formdata_and_abort_signal` | FormData có audio/lang/session |
| `voiceChatAPI` | `test_voice_chat_api_maps_server_error_message` | throw message thân thiện |
| `unifiedChatAPI` | `test_unified_chat_api_builds_text_image_audio_formdata` | FormData đủ fields |
| `unifiedChatAPI` | `test_unified_chat_api_timeout_or_abort` | AbortError handled |
| `submitFeedbackAPI` | `test_submit_feedback_api_payload_shape` | JSON đúng |
| `getMapConfigAPI` | `test_get_map_config_api_normalizes_artifacts` | response passthrough |
| `getRouteAPI` | `test_get_route_api_builds_query_params` | params lat/lng/lang đúng |
| `saveMapConfigAPI` | `test_save_map_config_api_posts_bounds_artifacts` | POST body đúng |
| `planTourAPI` | `test_plan_tour_api_builds_params` | params đúng |
| `getNextSuggestionAPI` | `test_next_suggestion_api_joins_visited_ids` | query `1,2,3` |
| Game APIs | `test_game_api_methods_validate_success_and_errors` | create/join/start/answer/next/end/status/praise/local-ip |
| Blog APIs | `test_blog_api_normalizes_camel_case_fields` | post fields đúng frontend |
| Blog APIs | `test_blog_api_parse_error_uses_detail_or_message` | throw rõ |

### 6.2. `frontend/src/services/tourMemoryService.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `createEmptyTourMemory` | `test_create_empty_memory_has_version_session_defaults` | field đủ |
| `normalizeArtifactForPassport` | `test_normalize_artifact_accepts_api_variants` | id/name/lat/lng đúng |
| `normalizeArtifactForPassport` | `test_normalize_artifact_rejects_missing_id` | null |
| `normalizeCatalogForPassport` | `test_normalize_catalog_deduplicates_ids` | unique |
| `loadTourMemory` | `test_load_memory_returns_empty_on_missing_invalid_completed` | empty |
| `saveTourMemory` | `test_save_memory_updates_timestamp_and_handles_quota` | không crash |
| `resetTourMemory` | `test_reset_memory_persists_new_session` | session mới |
| `clearTourMemory` | `test_clear_memory_removes_storage` | empty |
| `completeTourMemory` | `test_complete_memory_sets_completed_at` | completedAt |
| `recordCheckIn` | `test_record_checkin_first_and_repeat_visit` | visits tăng, route không duplicate |
| `recordPhoto` | `test_record_photo_limits_max_photos_and_cover` | max 10, cover đúng |
| `recordQuestion` | `test_record_question_limits_and_truncates` | max 40 |
| `recordAudio` | `test_record_audio_accumulates_seconds_and_limits` | total seconds |
| `buildTourSummary` | `test_build_tour_summary_progress_route_photos_audio` | progress đúng |
| `buildTourSummary` | đã có photo booth album test | giữ nguyên |

### 6.3. `frontend/src/utils/photoBoothCanvas.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `getPhotoFrameMaskBounds` | `test_get_mask_bounds_detects_largest_dark_region` | bounds đúng |
| `getPhotoFrameMaskBounds` | `test_get_mask_bounds_rejects_frame_without_dark_region` | throw |
| `preparePhotoBoothFrame` | `test_prepare_frame_caches_by_src` | load 1 lần |
| `preparePhotoBoothFrame` | `test_prepare_frame_deletes_cache_on_failure` | retry được |
| `composePhotoBoothImage` | `test_compose_photo_draws_camera_cover_and_overlay` | data URL |
| `optimizePhotoBoothImage` | `test_optimize_photo_resizes_and_quality` | <= max dimensions |
| `preloadPhotoBoothFrames` | `test_preload_frames_deduplicates_and_reports_failed` | total/ready/failed đúng |

### 6.4. `frontend/src/utils/photoBoothCamera.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `getPhotoBoothCameraStream` | `test_camera_stream_reuses_live_shared_stream` | không gọi getUserMedia lần 2 |
| `getPhotoBoothCameraStream` | `test_camera_stream_reuses_pending_promise` | tránh race |
| `getPhotoBoothCameraStream` | `test_camera_stream_stops_previous_dead_stream` | stop track cũ |
| `schedulePhotoBoothCameraRelease` | `test_schedule_camera_release_stops_after_delay` | track.stop |
| `releasePhotoBoothCameraStream` | `test_release_camera_stream_stops_immediately` | shared null |

### 6.5. `frontend/src/utils/imageUtils.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `compressImage` | `test_compress_image_keeps_aspect_ratio_landscape` | width <= max |
| `compressImage` | `test_compress_image_keeps_aspect_ratio_portrait` | height <= max |
| `compressImage` | `test_compress_image_rejects_load_error` | reject |
| `compressImage` | `test_compress_image_rejects_missing_canvas_context` | reject |

### 6.6. `frontend/src/hooks/useAudioRecorder.js`

Nếu thêm Vitest + React Testing Library hook test:

| Hàm/behavior | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `startRecording` | `test_audio_recorder_start_success` | isRecording true |
| `startRecording` | `test_audio_recorder_ignores_double_start` | getUserMedia gọi 1 lần |
| `startRecording` | `test_audio_recorder_permission_denied` | error `microphone_denied` |
| `startRecording` | `test_audio_recorder_device_missing` | error `microphone_not_found` |
| `stopRecording` | `test_audio_recorder_stop_creates_blob_and_stops_tracks` | tracks stop |
| timer | `test_audio_recorder_auto_stops_at_60_seconds` | duration 60 |
| `resetRecording` | `test_audio_recorder_reset_clears_blob_duration_error` | clear |
| unmount | `test_audio_recorder_cleanup_on_unmount` | stop/close |
| `getFilename` | `test_audio_recorder_filename_by_mime` | `.webm`, `.mp4`, `.ogg` |

### 6.7. `frontend/src/components/blog/blogLocalStorage.js`

| Hàm | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `getBlogInteraction` | `test_get_blog_interaction_default_false` | false/false |
| `setBlogInteraction` | `test_set_blog_interaction_persists_boolean_values` | localStorage đúng |
| `getBlogDraft` | `test_get_blog_draft_handles_bad_json` | null |
| `saveBlogDraft` | `test_save_blog_draft_adds_saved_at` | savedAt ISO |
| `clearBlogDraft` | `test_clear_blog_draft_removes_key` | removed |

### 6.8. Component test frontend cần có

| Component | Test case bắt buộc | Kỳ vọng |
|---|---|---|
| `App.jsx` | `test_app_initial_view_from_query_and_blog_path` | route đúng |
| `ExploreDashboard.jsx` | `test_dashboard_tabs_map_ask_passport_and_game_disabled_until_two_checkins` | tab/game state đúng |
| `UnifiedChatPage.jsx` | `test_chat_submit_text_adds_user_and_ai_message` | message list |
| `UnifiedChatPage.jsx` | `test_chat_handles_backend_error_without_white_screen` | error UI |
| `ChatComposer.jsx` | `test_chat_composer_disables_send_when_empty_or_loading` | disabled |
| `ChatMessageList.jsx` | `test_message_list_tts_buttons_reflect_play_pause` | aria/active |
| `MapExplore.jsx` | `test_map_route_success_draws_route_sheet` | route visible |
| `MapExplore.jsx` | `test_map_route_failure_shows_error` | không crash |
| `MapCalibrate.jsx` | `test_map_calibrate_loads_and_saves_config` | save API called |
| `GameHost.jsx` | `test_game_host_lobby_start_scoreboard_finish` | state đúng |
| `GamePlayer.jsx` | `test_game_player_join_answer_result` | answer flow |
| `NgocMonCheckout.jsx` | `test_checkout_validates_customer_and_calculates_total` | total đúng |
| `PaymentResult.jsx` | `test_payment_result_success_failed_missing_order` | UI đúng |
| `BlogEditorPage.jsx` | `test_blog_editor_validation_draft_publish` | validation/draft |
| `BlogDetailPage.jsx` | `test_blog_detail_like_bookmark_comment` | counts |
| `RatingSection.jsx` | `test_rating_submit_and_refresh_summary` | summary update |

---

## 7. E2E test tự động cho demo

Công cụ đề xuất: Playwright.

Tên file đề xuất:

- `frontend/e2e/smoke.spec.ts`
- `frontend/e2e/chat-voice-vision.spec.ts`
- `frontend/e2e/map-passport-photo.spec.ts`
- `frontend/e2e/game.spec.ts`
- `frontend/e2e/blog-rating-payment.spec.ts`
- `frontend/e2e/resilience.spec.ts`

### 7.1. E2E-01: vào app và chọn tour

1. Mở `https://localhost:5173`.
2. Xác nhận home hiển thị.
3. Chọn `Đại Nội Huế`.
4. Dashboard mở ở tab map.
5. Có 17 điểm trong catalog hoặc map config.
6. Không có console error nghiêm trọng.

Kỳ vọng:

- Header tour hiện đúng.
- Tab `Bản đồ`, `Hỏi AI`, `Passport` dùng được.
- Game disabled nếu chưa check-in đủ 2 điểm.

### 7.2. E2E-02: chat text + TTS + feedback

1. Mở dashboard tab `Hỏi AI`.
2. Nhập `Xin chào`.
3. Gửi.
4. AI trả lời template nhanh.
5. Bấm phát TTS.
6. Pause, resume, stop.
7. Gửi feedback helpful.

Kỳ vọng:

- Không gọi STT/Vision.
- Message user và AI xuất hiện đúng thứ tự.
- TTS state chuyển `playing -> paused -> playing -> idle`.
- Feedback thành công, không tạo duplicate UI state.

### 7.3. E2E-03: chat theo artifact context

1. Từ map chọn `Ngọ Môn`.
2. Bấm giới thiệu công trình.
3. App chuyển qua `Hỏi AI`.
4. Hỏi `Công trình này xây năm nào?`.
5. Hỏi tiếp `Ai xây?`.

Kỳ vọng:

- `artifact_id` được truyền qua chat.
- Câu sau hiểu `công trình này`.
- Có year/author nếu DB có.
- Không trả câu chung chung ngoài Huế.

### 7.4. E2E-04: upload ảnh nhận diện

Dữ liệu:

- `test_images/ngo_mon.jpg`
- `test_images/ngo_mon.png`
- `test_images/tank_843.jpg` hoặc ảnh không liên quan nếu cần negative

Các bước:

1. Mở tab chat.
2. Upload ảnh Ngọ Môn.
3. Gửi với câu hỏi `Ảnh này có chi tiết gì đáng chú ý?`.
4. Upload ảnh không liên quan.

Kỳ vọng:

- Ảnh Ngọ Môn trả artifact đúng hoặc yêu cầu xác nhận nếu confidence thấp.
- Câu trả lời bắt đầu từ quan sát ảnh, sau đó mới dùng lịch sử.
- Ảnh không liên quan trả message thân thiện, không 500.

### 7.5. E2E-05: ghi âm

1. Cấp quyền microphone.
2. Ghi âm câu `Giới thiệu Ngọ Môn`.
3. Dừng ghi âm.
4. Gửi.
5. Lặp lại với quyền microphone bị deny.

Kỳ vọng:

- Có transcript.
- Có câu trả lời.
- Audio duration không vượt 60s.
- Permission denied hiển thị hướng dẫn, không trắng màn hình.

### 7.6. E2E-06: bản đồ, route, arrival, passport

1. Mở map.
2. Chọn vị trí bắt đầu bằng pin hoặc GPS mock.
3. Chọn `Điện Thái Hòa`.
4. Bấm chỉ đường.
5. Xem route line và instruction sheet.
6. Bấm play/pause/resume hướng dẫn.
7. Bấm `Đã đến nơi`.
8. Mở Passport.

Kỳ vọng:

- Route hiển thị polyline.
- Instructions có ít nhất 1 bước.
- Arrival tạo check-in.
- Passport progress tăng.
- Nếu OSRM fail, fallback local/straight line vẫn có hướng dẫn.

### 7.7. E2E-07: gợi ý tour

1. Mở panel gợi ý lộ trình.
2. Chọn thời lượng 60 phút, 3 điểm.
3. Bấm tạo route.
4. Theo dõi điểm đầu tiên.
5. Xóa route.

Kỳ vọng:

- Route <= 3 stops.
- Có tổng thời gian, quãng đường.
- Marker route có số thứ tự.
- Xóa route dọn polyline/sheet.

### 7.8. E2E-08: photo booth

1. Check-in một điểm có frame.
2. Mở photo booth.
3. Cấp quyền camera.
4. Chụp ảnh.
5. Lưu vào passport.
6. Deny camera và thử lại.

Kỳ vọng:

- Frame load, vùng mask đúng.
- Ảnh lưu vào memory, không vượt quota.
- Deny camera có fallback/tải ảnh.
- Camera stream được release khi đóng modal.

### 7.9. E2E-09: game nhóm

1. Check-in ít nhất 2 địa điểm.
2. Bấm tạo game.
3. Nhập host nickname.
4. Mở URL join ở tab khác.
5. Player join.
6. Host start.
7. Player answer đúng/sai.
8. Host next.
9. Kết thúc game và lấy praise.

Kỳ vọng:

- Lobby có danh sách player.
- Không lộ đáp án trước scoreboard.
- Score đúng, scoreboard đúng.
- Praise chỉ sau khi finished.
- Nếu host auth chưa có, ghi rõ rủi ro trong demo.

### 7.10. E2E-10: blog

1. Mở `/blog`.
2. Search `Ngọ Môn`.
3. Filter tag.
4. Mở detail.
5. Like, bookmark.
6. Thêm comment hợp lệ.
7. Thử comment chứa `<script>`.
8. Mở `/blog/new`, lưu draft, publish.

Kỳ vọng:

- Search/filter không 500.
- Like/bookmark count cập nhật.
- Comment script bị chặn.
- Draft restore đúng.
- Post mới có slug unique.

### 7.11. E2E-11: rating

1. Mở destination detail có RatingSection.
2. Xem summary ban đầu.
3. Chọn service/scenery/price rating.
4. Nhập review.
5. Submit.
6. Xem summary/list update.

Kỳ vọng:

- Không cho rating ngoài 1..5.
- Review dài bị chặn.
- Summary update đúng.

### 7.12. E2E-12: payment sandbox

1. Mở checkout Ngọ Môn.
2. Tăng adult/children/food.
3. Nhập customer hợp lệ.
4. Submit.
5. Xác nhận redirect/popup VNPay sandbox.
6. Simulate return success/fail.
7. Mở payment result.

Kỳ vọng:

- Total đúng.
- Order code có format `VNP-*`.
- Payment result hiển thị success/fail.
- Missing order code hiển thị lỗi thân thiện.

### 7.13. E2E-13: resilience

1. Tắt backend.
2. Gửi chat.
3. Gọi map route.
4. Gửi rating/blog/payment.
5. Bật backend lại.

Kỳ vọng:

- UI hiện lỗi mất kết nối.
- Không trắng màn hình.
- Nút loading được reset.
- Retry được sau khi backend lên.

### 7.14. E2E-14: responsive/mobile

Viewport:

- Desktop: 1440x900
- Tablet: 768x1024
- Mobile: 390x844

Kỳ vọng:

- Text không tràn button/card.
- Map sheet không che hết marker quan trọng.
- Chat composer không bị keyboard mobile che.
- Payment bottom bar không che submit form.
- Blog/detail không vỡ layout.

---

## 8. Security test bắt buộc

### 8.1. Broken access control

| ID | Mục tiêu | Kịch bản | Kỳ vọng |
|---|---|---|---|
| SEC-01 | Map calibration | gọi `POST /api/v1/map/config` không auth | production phải 401/403 |
| SEC-02 | Game host action | player không phải host gọi start/next/end | phải 403 nếu triển khai host token |
| SEC-03 | Blog create | user bất kỳ tạo blog | nếu public thì rate limit/moderation, nếu admin thì auth |
| SEC-04 | Payment info | đoán order_code | không lộ PII quá mức, cân nhắc token |

### 8.2. Information disclosure

| ID | Mục tiêu | Kịch bản | Kỳ vọng |
|---|---|---|---|
| SEC-05 | Map config | `GET /api/v1/map/config` | không trả `google_maps_api_key` |
| SEC-06 | Local IP | `GET /api/v1/game/local-ip` | chỉ dev, production 404/403 |
| SEC-07 | Error handler | ép lỗi 500 ở router | không traceback, không `str(e)` raw chứa secret |
| SEC-08 | Stream error | voice SSE error | không lộ provider raw key/quota detail |
| SEC-09 | Health AI | `/api/v1/health/ai` | không public không rate limit |

### 8.3. Injection/XSS

| ID | Mục tiêu | Payload | Kỳ vọng |
|---|---|---|---|
| SEC-10 | Blog post | `<script>alert(1)</script>` | 422 backend |
| SEC-11 | Blog comment | `<img src=x onerror=alert(1)>` | 422 backend/frontend |
| SEC-12 | Game nickname | `<img src=x onerror=alert(1)>` | render text, không thực thi |
| SEC-13 | Rating review | `<script>alert(1)</script>` | render text, không thực thi |
| SEC-14 | Blog search | `' OR 1=1 --` | không 500, không bypass |
| SEC-15 | Artifact query | prompt injection trong chat | không lộ system prompt/db raw |

### 8.4. Payload abuse/rate limit

| ID | Endpoint | Kịch bản | Kỳ vọng |
|---|---|---|---|
| SEC-16 | `/api/v1/chat/unified` | 31 req/phút cùng IP | 429 |
| SEC-17 | `/api/v1/recognize` | ảnh base64 > 5MB | 413 trước provider |
| SEC-18 | `/api/v1/voice/chat` | audio > 8MB | 413 trước provider |
| SEC-19 | `/api/v1/voice/chat/stream` | audio > 8MB | P0: 413, cần bổ sung nếu fail |
| SEC-20 | `/api/v1/feedback` | spam feedback | nên 429 |
| SEC-21 | `/api/v1/health/ai` | spam deep check | nên 429 hoặc tắt |

### 8.5. Secret/config

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| SEC-22 | `.env` không được commit | `.gitignore` cover |
| SEC-23 | `.env.example` không chứa key thật | chỉ placeholder |
| SEC-24 | `settings.validate_runtime` production thiếu key | fail fast |
| SEC-25 | CORS production | chỉ allow domain thật, không wildcard |
| SEC-26 | Docker image | không chạy root nếu deploy production |

---

## 9. Performance và load test

Công cụ đề xuất: K6 hoặc Locust. Chạy trên staging/local có provider mock để không tốn quota.

### 9.1. Ngân sách hiệu năng

| Luồng | P95 mục tiêu | Ghi chú |
|---|---:|---|
| Health ready | < 300ms | DB local |
| Blog list/detail | < 500ms | DB seeded |
| Rating summary/list | < 500ms | DB seeded |
| Map config | < 700ms | 17 artifacts |
| Route fallback local | < 500ms | không OSRM |
| Chat greeting/template | < 800ms | không LLM |
| Chat RAG + LLM mock | < 2s | mock provider |
| Vision mock | < 1s | mock Gemini |
| Payment create | < 800ms | không gọi VNPay network, chỉ URL |

### 9.2. Load scenarios

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| PERF-01 | 50 VU đọc `/health`, `/map/config`, `/blog-posts` trong 5 phút | error < 1%, P95 đạt budget |
| PERF-02 | 30 VU gửi chat greeting/template | không 500, rate limit theo cấu hình |
| PERF-03 | 20 VU gửi feedback | DB pool không cạn |
| PERF-04 | 10 VU tạo payment order | order_code unique |
| PERF-05 | 20 VU poll game status | không race, không tăng RAM tuyến tính |
| PERF-06 | 24h soak test voice/chat stream mock | RAM không tăng tuyến tính |

### 9.3. Database performance

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| DB-PERF-01 | Seed 10.000 artifacts giả, fuzzy search không dấu | < 200ms nếu pg_trgm/index đúng |
| DB-PERF-02 | Blog search 10.000 posts | < 300ms hoặc cần index |
| DB-PERF-03 | Rating summary 100.000 rows | < 500ms hoặc cần aggregate/index |
| DB-PERF-04 | ChatTurn session 10.000 turns | recent context chỉ lấy limit, không scan full |

---

## 10. Manual demo rehearsal

### 10.1. Chuẩn bị trước demo

- [ ] PostgreSQL chạy.
- [ ] Alembic migration đã chạy.
- [ ] Seed data 17 công trình đã chạy.
- [ ] Backend ready trả 200.
- [ ] Frontend chạy HTTPS.
- [ ] Camera/microphone browser được cấp quyền.
- [ ] API key Gemini/Groq còn quota.
- [ ] Ảnh test trong `test_images/` mở được.
- [ ] Browser cache/localStorage/sessionStorage đã reset nếu muốn demo sạch.

### 10.2. Kịch bản demo 20 đến 30 phút

1. Mở app, chọn Đại Nội Huế.
2. Chọn Ngọ Môn trên map, xem stop sheet.
3. Bấm chỉ đường tới Điện Thái Hòa.
4. Bấm nghe hướng dẫn, pause/resume.
5. Bấm đã đến nơi, xác nhận passport tăng.
6. Chuyển sang Hỏi AI, hỏi `Công trình này có ý nghĩa gì?`.
7. Upload ảnh Ngọ Môn, hỏi `Ảnh này có chi tiết gì đáng chú ý?`.
8. Ghi âm `Giới thiệu Điện Kiến Trung`.
9. Bấm feedback helpful.
10. Check-in điểm thứ hai, tạo game.
11. Mở player join, trả lời 1 câu.
12. Mở Passport/Trip Journal, xem ảnh/câu hỏi/audio.
13. Mở Blog, search, like/comment.
14. Mở Rating, gửi review.
15. Mở checkout Ngọ Môn, tạo payment order sandbox.

### 10.3. Kịch bản lỗi chủ động trong demo nội bộ

- [ ] Tắt backend, gửi chat: UI phải báo mất kết nối.
- [ ] Deny microphone: UI báo lỗi quyền mic.
- [ ] Deny camera: photo booth không crash.
- [ ] Upload ảnh không liên quan: AI trả không nhận diện.
- [ ] Nhập blog comment script: bị chặn.
- [ ] VNPay return thiếu signature: payment result failed.

---

## 11. P0 backlog cần ưu tiên viết test/sửa trước demo

### 11.1. Backend P0

- [ ] Thêm test và sửa `voice_chat_stream` để validate audio size trước provider.
- [ ] Thêm test không lộ `google_maps_api_key` trong `/api/v1/map/config`.
- [ ] Khóa hoặc ẩn `POST /api/v1/map/config` trên production.
- [ ] Thêm upper bound cho `/api/v1/map/plan-tour`: ví dụ `max_duration <= 480`, `max_places <= 17`.
- [ ] Chuẩn hóa test DB fixture, tránh test ghi vào DB thật.
- [ ] Thêm security test không lộ traceback từ all routers.
- [ ] Thêm API tests cho payment/blog/rating vì các luồng này đang ít coverage.

### 11.2. Frontend P0

- [ ] Thêm test mocked fetch cho `unifiedChatAPI`, `getRouteAPI`, `planTourAPI`, `submitFeedbackAPI`.
- [ ] Thêm E2E smoke: home -> dashboard -> map -> chat -> feedback.
- [ ] Thêm E2E backend down không trắng màn hình.
- [ ] Test quyền microphone/camera denied.
- [ ] Chạy screenshot responsive 390x844, 768x1024, 1440x900 trước demo.

### 11.3. Demo P0

- [ ] Chuẩn bị 3 ảnh demo: Ngọ Môn rõ, Điện Thái Hòa rõ, ảnh không liên quan.
- [ ] Chuẩn bị sẵn 5 câu hỏi text để tránh phụ thuộc STT nếu môi trường ồn.
- [ ] Chuẩn bị fallback nếu provider AI hết quota: dùng câu hỏi greeting/template, map/passport/blog/payment.
- [ ] Ghi lại trạng thái health/ready trước khi demo.

---

## 12. Checklist pass/fail cuối cùng

### 12.1. Automation

- [ ] `pytest backend/tests -q` pass.
- [ ] `npm run build` pass.
- [ ] `npm run lint` pass hoặc chỉ còn warning đã chấp nhận.
- [ ] `npm run test:web-speech` pass.
- [ ] `npm run test:photo-booth` pass.
- [ ] Playwright smoke pass nếu đã bổ sung.

### 12.2. Smoke thủ công

- [ ] Health ready 200.
- [ ] Home/dashboard mở được.
- [ ] Chat text trả lời được.
- [ ] Upload ảnh trả lời được.
- [ ] Ghi âm trả lời được hoặc permission error rõ.
- [ ] Map route hoạt động hoặc fallback.
- [ ] Passport check-in hoạt động.
- [ ] Game tạo phòng hoạt động.
- [ ] Blog list/detail hoạt động.
- [ ] Rating submit hoạt động.
- [ ] Payment create hoạt động.

### 12.3. Security tối thiểu

- [ ] Không lộ API key trong response.
- [ ] Không lộ traceback.
- [ ] Payload quá lớn bị chặn.
- [ ] XSS blog/comment/game nickname không thực thi.
- [ ] Calibration map không public nếu demo online.
- [ ] Deep health AI không public nếu demo online.

---

## 13. Thứ tự triển khai test đề xuất

1. Viết/sửa P0 backend validation/security tests.
2. Chuẩn hóa database test fixture.
3. Bổ sung API contract tests cho payment/blog/rating/map config.
4. Bổ sung frontend service tests cho `apiService.js`.
5. Bổ sung Playwright smoke cho 3 luồng: chat, map/passport, payment/blog/rating.
6. Chạy rehearsal nội bộ đủ kịch bản demo.
7. Chỉ sau khi pass mới demo với người dùng thật.

Ghi chú quan trọng: tài liệu này là kịch bản kiểm thử, không phải cam kết hệ thống hiện đã pass toàn bộ. Những mục được đánh dấu P0/P1 có thể phát hiện lỗi thật trong code hiện tại và cần được xử lý trước khi public demo.
