import json
import os
import logging

class Translator:
    """
    Handles i18n using JSON files.
    """
    _translations = {}
    _current_lang = "fr"
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOCALES_DIR = os.path.join(BASE_DIR, 'locales')

    @classmethod
    def load_language(cls, lang_code):
        """
        Load the JSON file for the requested language.
        """
        filepath = os.path.join(cls.LOCALES_DIR, f"{lang_code}.json")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Language file not found: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cls._translations = json.load(f)
            
            cls._current_lang = lang_code
            logging.info(f"Language loaded: {lang_code}")
            return True
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"The {lang_code}.json file is malformed", e.doc, e.pos)
        except Exception as e:
            raise RuntimeError(f"Unable to load language: {e}")

    @classmethod
    def tr(cls, key):
        """
        Return the translation for the key or the key itself if missing.
        """
        return cls._translations.get(key, key)

    @classmethod
    def get_current_lang(cls):
        return cls._current_lang