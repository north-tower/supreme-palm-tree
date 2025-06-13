import json
import os
from typing import Dict, Optional

class LanguageManager:
    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_languages()

    def load_languages(self):
        """Load all language files from the languages directory"""
        languages_dir = "languages"
        if not os.path.exists(languages_dir):
            os.makedirs(languages_dir)

        # Load each language file
        for filename in os.listdir(languages_dir):
            if filename.endswith(".json"):
                language_code = filename[:-5]  # Remove .json extension
                with open(os.path.join(languages_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)

    def set_language(self, language_code: str) -> bool:
        """Set the current language"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False

    def get_text(self, key: str, default: Optional[str] = None) -> str:
        """Get translated text for the given key"""
        try:
            return self.translations[self.current_language][key]
        except KeyError:
            # Try default language if current language doesn't have the key
            try:
                return self.translations[self.default_language][key]
            except KeyError:
                return default if default is not None else key

    def get_available_languages(self) -> list:
        """Get list of available language codes"""
        return list(self.translations.keys())

    def add_translation(self, language_code: str, key: str, text: str):
        """Add or update a translation"""
        if language_code not in self.translations:
            self.translations[language_code] = {}
        self.translations[language_code][key] = text
        self._save_language(language_code)

    def _save_language(self, language_code: str):
        """Save language file to disk"""
        with open(f"languages/{language_code}.json", 'w', encoding='utf-8') as f:
            json.dump(self.translations[language_code], f, ensure_ascii=False, indent=4) 