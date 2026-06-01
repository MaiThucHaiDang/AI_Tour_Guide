"""Language context mapping helpers for voice services.

Moved from: part4/backend/services/voice/language_manager.py
Logic preserved exactly.
"""


class LanguageManager:
    """Resolve language-specific database and UI settings."""

    def setup_context(self, lang_param: str) -> dict[str, str]:
        normalized_lang = lang_param.strip().lower()
        for separator in ("-", "_"):
            if separator in normalized_lang:
                normalized_lang = normalized_lang.split(separator)[0]
                break

        if normalized_lang == "vi":
            return {
                "db_field": "history_text_vi",
                "ui_locale": "vi-VN",
                "lang_code": "vi",
            }
        if normalized_lang == "en":
            return {
                "db_field": "history_text_en",
                "ui_locale": "en-US",
                "lang_code": "en",
            }

        raise ValueError("Unsupported language. Expected 'vi' or 'en'.")
