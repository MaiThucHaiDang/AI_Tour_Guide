"""Language context mapping helpers for voice services.

Moved from: part4/backend/services/voice/language_manager.py
Logic preserved exactly.
"""

import threading


class LanguageManager:
    """Resolve language-specific database and UI settings (Singleton)."""
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - ensure only one instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def setup_context(self, lang_param: str) -> dict[str, str]:
        """Setup language-specific context.
        
        Args:
            lang_param: Language code (e.g., 'vi', 'en', 'vi-VN', 'en_US')
            
        Returns:
            Dictionary with db_field, ui_locale, and lang_code
            
        Raises:
            ValueError: If language is not supported
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


def get_language_manager() -> LanguageManager:
    """Dependency provider for LanguageManager."""
    return LanguageManager()
