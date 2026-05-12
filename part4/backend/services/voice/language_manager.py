"""Language context mapping helpers for voice services."""


class LanguageManager:
    """Resolve language-specific database and UI settings."""

    def setup_context(self, lang_param: str) -> dict[str, str]:
        """Return language-specific context settings.

        Args:
            lang_param: Language code, expected to be ``vi`` or ``en``.

        Returns:
            A dictionary containing the database field and UI locale.

        Raises:
            ValueError: If ``lang_param`` is not supported.
        """
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