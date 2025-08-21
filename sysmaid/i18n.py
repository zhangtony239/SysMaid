import json
import locale
import os
from typing import Dict

_translations: Dict[str, str] = {}


def _load_language():
    """
    Loads the language file based on the system's default locale.
    Falls back to en_US if the specific language file is not found.
    """
    global _translations
    try:
        # e.g., 'zh_CN' or 'en_US'
        lang_code, _ = locale.getdefaultlocale()
    except (ValueError, TypeError):
        lang_code = 'en_US'  # Default fallback

    if lang_code is None:
        lang_code = 'en_US'

    base_dir = os.path.dirname(__file__)
    lang_file_path = os.path.join(base_dir, 'i18n', f'{lang_code}.json')

    # Fallback to en_US if the specific language file doesn't exist
    fallback_path = os.path.join(base_dir, 'i18n', 'en_US.json')
    if not os.path.exists(lang_file_path):
        lang_file_path = fallback_path

    try:
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            _translations = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If any error occurs during loading, even with the fallback,
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