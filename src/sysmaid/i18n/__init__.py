# nuitka-project: --include-package=sysmaid.i18n

import importlib
import locale
from typing import Dict

_translations: Dict[str, str] = {}


def _load_language():
    """
    Loads the language module based on the system's default locale.
    Falls back to en_us if the specific language module is not found.
    """
    global _translations
    try:
        # e.g., 'zh_CN' or 'en_US'
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            lang_code = lang_code.lower()
        else:
            lang_code = 'en_us'
    except (ValueError, TypeError):
        lang_code = 'en_us'  # Default fallback

    if lang_code is None:
        lang_code = 'en_us'

    try:
        # Dynamically import the language module
        lang_module = importlib.import_module(f'.{lang_code}', __name__)
        _translations = lang_module.translations
    except (ImportError, AttributeError):
        # Fallback to en_us if the specific language module doesn't exist or is invalid
        try:
            lang_module = importlib.import_module('.en_us', __name__)
            _translations = lang_module.translations
        except (ImportError, AttributeError):
            # If any error occurs, even with the fallback,
            # use an empty dict to prevent crashes.
            _translations = {}


def get_text(key: str) -> str:
    """
    Returns the translated text for a given key.
    If the key is not found, it returns the key itself as a fallback.
    """
    return _translations.get(key, key)


# Load the appropriate language when the module is first imported.
_load_language()