import pytest
import threading
from concurrent.futures import ThreadPoolExecutor

from utils.language_manager import LanguageManager, get_language_manager

def test_language_manager_is_singleton():
    """Test that consecutive creations return the same object."""
    manager1 = LanguageManager()
    manager2 = LanguageManager()
    manager3 = get_language_manager()
    
    assert manager1 is manager2
    assert manager1 is manager3

def test_language_manager_singleton_thread_safe():
    """Robust test to ensure singleton pattern holds under concurrent access."""
    # Reset singleton state for this specific test
    LanguageManager._instance = None
    
    instances = []
    
    def get_instance():
        instances.append(LanguageManager())

    # Create 50 threads trying to instantiate it simultaneously
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(get_instance) for _ in range(50)]
        for f in futures:
            f.result()
            
    assert len(instances) == 50
    # All instances should be identical
    first_instance = instances[0]
    for inst in instances:
        assert inst is first_instance

@pytest.mark.parametrize("vi_input", [
    "vi",
    "vi-VN",
    "vi_VN",
    " VI ",
    "vi-vn",
    "VI_vn",
])
def test_setup_context_vi_variants(vi_input):
    """Test mapping for Vietnamese language variants."""
    manager = get_language_manager()
    
    expected = {
        "db_field": "history_text_vi",
        "ui_locale": "vi-VN",
        "lang_code": "vi",
    }
    
    assert manager.setup_context(vi_input) == expected

@pytest.mark.parametrize("en_input", [
    "en",
    "en-US",
    "en_US",
    " EN ",
    "en-GB",
    "EN_ca",
])
def test_setup_context_en_variants(en_input):
    """Test mapping for English language variants."""
    manager = get_language_manager()
    
    expected = {
        "db_field": "history_text_en",
        "ui_locale": "en-US",
        "lang_code": "en",
    }
    
    assert manager.setup_context(en_input) == expected

@pytest.mark.parametrize("unsupported_input", [
    "fr",
    "de-DE",
    "invalid_lang",
    "",
    "   ",
])
def test_setup_context_rejects_unsupported(unsupported_input):
    """Test that unsupported language codes raise ValueError."""
    manager = get_language_manager()
    
    with pytest.raises(ValueError, match="Unsupported language"):
        manager.setup_context(unsupported_input)
